#include <WiFi.h>
#include <PubSubClient.h>
#include <EmonLib.h>

EnergyMonitor emon1;

const char *ssid = "";
const char *password = "";
const char *mqtt_server = "";
const char *mqtt_topic = "topico/corrente";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.begin(115200);
  Serial.println();

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.println("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando ao Broker MQTT...");
    
    if (client.connect("ESP32Client")) {
      Serial.println("Conectado");
    } else {
      Serial.print("Falha, rc=");
      Serial.print(client.state());
      Serial.println(" Tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

void setup() {
  emon1.current(36, 0.8);  // Pino A0 e fator de calibração
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }

  double corrente = emon1.calcIrms();  // Obter a corrente eficaz (RMS)

  Serial.print("Corrente: ");
  Serial.print(corrente);
  Serial.println(" A");

  char correnteStr[10];
  dtostrf(corrente, 4, 2, correnteStr);

  client.publish(mqtt_topic, correnteStr);

  delay(1000);
}
