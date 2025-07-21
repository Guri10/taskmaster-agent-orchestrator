// Program.cs - TaskMaster.Api
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapPost("/task", async (HttpContext context) =>
{
    // Read instruction from request body (not used in static response)
    var request = await JsonSerializer.DeserializeAsync<JsonElement>(context.Request.Body);
    // Return static JSON mimicking agent output
    var response = new[]
    {
        new {
            ticker = "AAPL",
            date = "2025-07-21",
            open = 212.05,
            high = 215.78,
            low = 211.64,
            close = 212.32,
            sma20 = 208.03
        }
    };
    context.Response.ContentType = "application/json";
    await context.Response.WriteAsync(JsonSerializer.Serialize(response));
});

app.MapGet("/metrics", (HttpContext context) =>
{
    // Return static Prometheus metrics
    context.Response.ContentType = "text/plain";
    return context.Response.WriteAsync("agent_success_total 1\nagent_latency_seconds 0.123\nagent_errors_total 0\n");
});

app.Run(); 