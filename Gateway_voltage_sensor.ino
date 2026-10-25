#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "Drey";
const char* password = "YOUR_PASSWORD"; // Change this to your real password on your laptop

WebServer server(80);
const int SENSOR_PIN = 34;
const float VOLTS_PER_MV = 0.0867; 

float readVolts() {
  const int N = 400;
  double sum = 0, sumSq = 0;
  for (int i = 0; i < N; i++) {
    double mv = analogReadMilliVolts(SENSOR_PIN);
    sum += mv;
    sumSq += mv * mv;
    delayMicroseconds(500);
  }
  double mean = sum / N;
  double rmsMv = sqrt(sumSq / N - mean * mean);
  return rmsMv * VOLTS_PER_MV;
}

void setup() {
  Serial.begin(115200);
  IPAddress local_IP(192, 168, 10, 103); // Gateway is .103
  IPAddress gateway(192, 168, 10, 1);
  IPAddress subnet(255, 255, 255, 0);

  WiFi.config(local_IP, gateway, subnet);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println(WiFi.localIP());

  server.on("/", []() {
    server.send(200, "text/plain", String(readVolts(), 2));
  });
  server.begin();
}

void loop() {
  server.handleClient();
}