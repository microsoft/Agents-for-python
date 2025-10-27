using Microsoft.Agents.Core.Models;
using Microsoft.Agents.Core.Serialization;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Identity.Web;
using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text.Json;

namespace Framework
{
    public sealed class BotResponse : IAsyncDisposable
    {
        readonly WebApplication _app;
        ConcurrentDictionary<string, List<Activity>> _multipleActivities = new();
        public string TestId { get; } = Guid.NewGuid().ToString();
        public BotResponse()
        {
            // Suppress console output
            Console.SetOut(TextWriter.Null);

            // Create a web application builder and configure services
            WebApplicationBuilder builder = WebApplication.CreateBuilder();

            builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
                    .AddMicrosoftIdentityWebApi(builder.Configuration);

            // Add services to the web application
            _app = builder.Build();
            _app.UseRouting();
            _app.MapPost("/v3/conversations/{*text}", async (ctx) =>
            {

                using StreamReader reader = new(ctx.Request.Body);
                var resp = await reader.ReadToEndAsync();
                Activity act = ProtocolJsonSerializer.ToObject<Activity>(resp);
                string cid = act.Conversation.Id;
                var activityList = _multipleActivities.GetOrAdd(cid!, _ => new List<Activity>());

                lock (activityList)
                {
                    activityList.Add(act);
                }

                var response = new
                {
                    Id = Guid.NewGuid().ToString()
                };

                // Check if the activity is a streamed activity
                if (act.Entities?.Any(e => e.Type == EntityTypes.StreamInfo) == true)
                {
                    var entities = ProtocolJsonSerializer.ToJson(act.Entities[0]);
                    var sact = ProtocolJsonSerializer.ToObject<StreamInfo>(entities);

                    bool handled = HandleStreamedActivity(act, sact, cid);

                    ctx.Response.StatusCode = 200;
                    ctx.Response.ContentType = "application/json";
                    await ctx.Response.WriteAsync(JsonSerializer.Serialize(response));

                    if (BotClient.TaskList.TryGetValue(cid!, out var tcs) && handled)
                    {
                        if (_multipleActivities.TryGetValue(cid, out var streamedActivity))
                        {
                            tcs!.TrySetResult(streamedActivity.ToArray());
                            _multipleActivities.TryRemove(cid, out _);
                        }
                    }
                }
                else
                {

                    if (act.Type != ActivityTypes.Typing)
                    {
                        _ = Task.Run(async () =>
                        {
                            await Task.Delay(5000);
                            if (BotClient.TaskList.TryGetValue(cid!, out var tcs))
                            {
                                _multipleActivities.TryGetValue(cid!, out var result);
                                tcs?.TrySetResult(result!.ToArray());
                            }
                        });
                    }
                    ctx.Response.StatusCode = 200;
                    ctx.Response.ContentType = "application/json";
                    await ctx.Response.WriteAsync(JsonSerializer.Serialize(response));
                }
            });

            ServiceEndpoint = "http://localhost:9873";

            _app.UseAuthentication();
            _app.UseAuthorization();
            _app.RunAsync(ServiceEndpoint);
        }

        private bool HandleStreamedActivity(Activity act, StreamInfo sact, string cid)
        {

            // Check if activity is the final message 
            if (sact.StreamType == StreamTypes.Final)
            {
                if (act.Type == ActivityTypes.Message)
                {
                    return true;
                }
                else
                {
                    throw new Exception("final streamed activity should be type message");
                }
            }

            // Handler for streaming types which allows us to verify later if the text length has increased
            else if (sact.StreamType == StreamTypes.Streaming)
            {
                if (sact.StreamSequence <= 0 && act.Type == ActivityTypes.Typing)
                {
                    throw new Exception("streamed activity's stream sequence should be a positive number");
                }
            }
            // Activity is being streamed but isn't the final message
            return false;

        }

        public async ValueTask DisposeAsync()
        {
            await _app.StopAsync();
            await _app.DisposeAsync();
        }

        public string ServiceEndpoint { get; private set; }

    }

}