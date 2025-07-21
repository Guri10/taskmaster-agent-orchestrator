// Program.cs - TaskMaster.Api
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
using System.Text.Json;
using System.Diagnostics;
using System.IO;
using System.Collections.Concurrent;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Metrics storage
long agentSuccessTotal = 0;
long agentErrorsTotal = 0;
ConcurrentBag<double> agentLatencies = new();

app.MapPost("/task", async (HttpContext context) =>
{
    var sw = Stopwatch.StartNew();
    bool success = false;
    try
    {
        var request = await JsonSerializer.DeserializeAsync<JsonElement>(context.Request.Body);
        string instruction = request.GetProperty("instruction").GetString() ?? "";

        var psi = new ProcessStartInfo
        {
            FileName = "python3",
            WorkingDirectory = Path.Combine(Directory.GetCurrentDirectory(), "../../.."),
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        psi.ArgumentList.Add("agent/main.py");
        psi.ArgumentList.Add(instruction);

        using var process = Process.Start(psi);
        string output = await process.StandardOutput.ReadToEndAsync();
        string error = await process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        if (process.ExitCode != 0)
        {
            context.Response.StatusCode = 500;
            agentErrorsTotal++;
            agentLatencies.Add(sw.Elapsed.TotalSeconds);
            await context.Response.WriteAsync(JsonSerializer.Serialize(new { error = error.Trim() }));
            return;
        }
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(output);
        success = true;
    }
    catch (Exception ex)
    {
        context.Response.StatusCode = 500;
        agentErrorsTotal++;
        await context.Response.WriteAsync(JsonSerializer.Serialize(new { error = ex.Message }));
    }
    finally
    {
        agentLatencies.Add(sw.Elapsed.TotalSeconds);
        if (success) agentSuccessTotal++;
    }
});

app.MapGet("/metrics", (HttpContext context) =>
{
    context.Response.ContentType = "text/plain";
    // Prometheus metrics format
    var lines = new List<string>
    {
        "# HELP agent_latency_seconds Latency of agent requests in seconds",
        "# TYPE agent_latency_seconds histogram"
    };
    // Histogram buckets (seconds)
    double[] buckets = { 0.5, 1, 2, 5, 10 };
    var counts = new int[buckets.Length];
    foreach (var latency in agentLatencies)
    {
        for (int i = 0; i < buckets.Length; i++)
        {
            if (latency <= buckets[i])
            {
                counts[i]++;
                break;
            }
        }
    }
    int cumulative = 0;
    for (int i = 0; i < buckets.Length; i++)
    {
        cumulative += counts[i];
        lines.Add($"agent_latency_seconds_bucket{{le=\"{buckets[i]}\"}} {cumulative}");
    }
    lines.Add($"agent_latency_seconds_bucket{{le=\"+Inf\"}} {agentLatencies.Count}");
    lines.Add($"agent_latency_seconds_sum {agentLatencies.Sum()}");
    lines.Add($"agent_latency_seconds_count {agentLatencies.Count}");
    lines.Add("# HELP agent_success_total Total successful agent requests");
    lines.Add("# TYPE agent_success_total counter");
    lines.Add($"agent_success_total {agentSuccessTotal}");
    lines.Add("# HELP agent_errors_total Total failed agent requests");
    lines.Add("# TYPE agent_errors_total counter");
    lines.Add($"agent_errors_total {agentErrorsTotal}");
    return context.Response.WriteAsync(string.Join("\n", lines) + "\n");
});

app.Run(); 