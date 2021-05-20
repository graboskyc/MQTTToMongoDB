using System;
using System.Threading.Tasks;
using Nito.AsyncEx;
using MongoDB.Driver;
using MongoDB.Bson;
using MQTTnet;
using MQTTnet.Server;
using System.Text;

namespace MQTTToMongoDB
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Opening...");

            // parse cli args
            if (args.Length != 1)
            {
                Console.WriteLine("Need 1 arg: Connection string for MongoDB");
                return;
            }

            var connStr = args[0];
            //var connStr = "mongodb://root:root123@localhost:27100";

            StartAsync(connStr).Wait();
        }

        private static async Task StartAsync(string connStr)
        {
            // mongodb setup
            MongoClient dbClient = new MongoClient(connStr);
            var db = dbClient.GetDatabase("messages");
            var col = db.GetCollection<BsonDocument>("messages");

            // mqtt setup
            var optionsBuilder = new MqttServerOptionsBuilder()
                .WithConnectionBacklog(100)
                .WithDefaultEndpointPort(1883)
                .WithApplicationMessageInterceptor(context =>
                {
                    context.AcceptPublish = true;
                    HandleNewMessage(context, col);
                });

            var mqttServer = new MqttFactory().CreateMqttServer();
            await mqttServer.StartAsync(optionsBuilder.Build());

            // wait forever
            Console.WriteLine("Press any key to exit.");
            Console.ReadLine();

            // cleanup
            await mqttServer.StopAsync();
        }

        private static void HandleNewMessage(MqttApplicationMessageInterceptorContext context, IMongoCollection<BsonDocument> handle)
        {
            Console.WriteLine("Got message!");

            var payload = context.ApplicationMessage?.Payload == null ? null : Encoding.UTF8.GetString(context.ApplicationMessage?.Payload);

            var newDoc = new BsonDocument {
                { "device", context.ClientId },
                { "reading", Int32.Parse(payload) },
            };

            handle.InsertOne(newDoc);

            Console.WriteLine("\tWritten!");
        }
    }
}
