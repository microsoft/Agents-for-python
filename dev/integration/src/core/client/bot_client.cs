using Microsoft.Agents.Core.Models;
using Microsoft.Agents.Core.Serialization;
using Microsoft.Identity.Client;
using System.Collections.Concurrent;
using System.Text.Json;

namespace Framework
{
    public class BotClient(string messagingEndpoint, string serviceEndpoint, string cid, string clientId, string tenantId, string clientSecret)
    {
        public static ConcurrentDictionary<string, TaskCompletionSource<Activity[]>> TaskList = new();

        public async Task<string> SendRequest(Activity activity)
        {

            // Create bearer authentication token
            IConfidentialClientApplication app = ConfidentialClientApplicationBuilder
                .Create(clientId)
                .WithTenantId(tenantId)
                .WithClientSecret(clientSecret)
                .Build();

            var token = await app.AcquireTokenForClient([clientId + "/.default"]).ExecuteAsync();

            // Send request to agent
            HttpClient http = new();

            // Update activity to send to service endpoint
            activity.ServiceUrl = serviceEndpoint;

            // Update activity conversation ID
            activity.Conversation.Id = cid;

            var stringContent = new StringContent(activity.ToJson(), System.Text.Encoding.UTF8, "application/json");

            HttpRequestMessage req = new(HttpMethod.Post, messagingEndpoint)
            {
                Headers =
                {
                    { "Authorization", "Bearer " + token.AccessToken }
                },
                Content = stringContent

            };

            var resp = await http.SendAsync(req);

            // Check if request was successful
            if (!resp.IsSuccessStatusCode)
            {
                throw new Exception("Failed to send activity: " + resp.StatusCode);
            }

            var content = await resp.Content.ReadAsStringAsync();
            return content;
        }
        public async Task<Activity[]> SendActivity(Activity activity)
        {

            // Keep track of activities being sent to the web service
            TaskCompletionSource<Activity[]> tcs = new();

            TaskList.TryAdd(cid, tcs);

            // Send activity to the agent
            var content = await SendRequest(activity);

            // Receive response from the agent 
            var result = await tcs.Task.WaitAsync(TimeSpan.FromSeconds(20));
            TaskList.TryRemove(cid, out _);

            return result;
        }

        public async Task<Activity[]> SendExpectRepliesActivity(Activity activity)
        {
            // Validate that the activity is of delivery mode expected replies
            if (activity.DeliveryMode != DeliveryModes.ExpectReplies)
            {
                throw new InvalidOperationException("Activity type must be ExpectedReplies.");
            }

            // Keep track of activities being sent to the web service
            TaskCompletionSource<Activity[]> tcs = new();

            // Send activity to the agent
            var content = await SendRequest(activity);

            // Receive response from the agent 
            if (content.Length == 0)
            {
                throw new InvalidOperationException("No response received from the agent.");
            }
            JsonDocument jsonDoc = JsonDocument.Parse(content);
            JsonElement activitiesJson = jsonDoc.RootElement.GetProperty("activities");
            var activities = ProtocolJsonSerializer.ToObject<Activity[]>(activitiesJson);

            return activities;

        }

        public async Task<Activity[]> SendStreamActivity(Activity activity)
        {
            // Validate that the activity is of type Stream
            if (activity.DeliveryMode != DeliveryModes.Stream)
            {
                throw new InvalidOperationException("Activity type must be Stream.");
            }

            // Keep track of activities being sent to the web service
            TaskCompletionSource<Activity[]> tcs = new();

            TaskList.TryAdd(cid, tcs);

            // Send activity to the agent
            var content = await SendRequest(activity);

            // Check if error comes back
            if (content.Length == 0) { 
                var result = await tcs.Task.WaitAsync(TimeSpan.FromSeconds(6));
                if (result.Length > 0)
                {
                    return result;
                }
            }

            // Receive response from the agent 
            if (content.Length == 0)
            {
                throw new InvalidOperationException("No response received from the agent.");
            }

            var split = content.Split("\n\r\n");
            split = split.Where(s => !string.IsNullOrWhiteSpace(s)).ToArray();

            Activity[] activities = new Activity[split.Length];

            for (int i = 0; i < split.Length; i++)
            {
                if (split[i].Contains("event: activity"))
                {
                    var format = split[i].Split("data: ");
                    var act = ProtocolJsonSerializer.ToObject<Activity>(format[1]);
                    activities[i] = act;
                } else
                {
                    throw new Exception("Must receive server-sent events");
                }
            }

            TaskList.TryRemove(cid, out _);

            return activities;
        }


        public async Task<string> SendInvoke(Activity activity)
        {

            // Validate that the activity is of type Invoke
            if (activity.Type != ActivityTypes.Invoke)
            {
                throw new InvalidOperationException("Activity type must be Invoke.");
            }

            // Send activity to the agent
            var content = await SendRequest(activity);

            return content;
        }
    }
}