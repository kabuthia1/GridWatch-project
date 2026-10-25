#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "WIFI_PASSWORD";
const char* password = "YOUR_PASSWORD"; // Change this to your real password on your laptop

WebServer server(80);
const int SENSOR_PIN = 34;
const float MV_PER_AMP = 185.0; 

float readCurrentA() {
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
  return rmsMv / MV_PER_AMP;
}

void setup() {
  Serial.begin(115200);
  IPAddress local_IP(192, 168, 10, 104); // NODE 1 IS .105
  IPAddress gateway(192, 168, 10, 1);
  IPAddress subnet(255, 255, 255, 0);

  WiFi.config(local_IP, gateway, subnet);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println(WiFi.localIP());

  server.on("/", []() {
    server.send(200, "text/plain", String(readCurrentA(), 3));
  });
  server.begin();
}

void loop() {
  server.handleClient();
}
