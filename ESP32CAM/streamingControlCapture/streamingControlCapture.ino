#include "esp_camera.h"
#include <WiFi.h>
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"
#include "fb_gfx.h"
#include "soc/soc.h" 
#include "soc/rtc_cntl_reg.h"  
#include "esp_http_server.h"

// Configurações da rede Wi-Fi
const char* ssid = "";
const char* password = "";

// Definições dos pinos da câmera (ajuste conforme o modelo do seu ESP32CAM)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Defina o pino da saída digital livre para uso
#define OUTPUT_GPIO_NUM   12  // Escolha um pino disponível no seu ESP32CAM

#define PART_BOUNDARY "123456789000000000000987654321"

static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// Variável global para o servidor HTTP
httpd_handle_t stream_httpd = NULL;

// Manipulador para o streaming de vídeo
static esp_err_t stream_handler(httpd_req_t *req){
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if(res != ESP_OK){
    return res;
  }

  while(true){
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Falha na captura da câmera");
      res = ESP_FAIL;
    } else {
      if(fb->width > 400){
        if(fb->format != PIXFORMAT_JPEG){
          bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
          esp_camera_fb_return(fb);
          fb = NULL;
          if(!jpeg_converted){
            Serial.println("Falha na compressão JPEG");
            res = ESP_FAIL;
          }
        } else {
          _jpg_buf_len = fb->len;
          _jpg_buf = fb->buf;
        }
      }
    }
    if(res == ESP_OK){
      size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    }
    if(res == ESP_OK){
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    if(res == ESP_OK){
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
    }
    if(fb){
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if(_jpg_buf){
      free(_jpg_buf);
      _jpg_buf = NULL;
    }
    if(res != ESP_OK){
      break;
    }
  }
  return res;
}

// Manipulador para controlar a saída digital via HTTP
static esp_err_t control_handler(httpd_req_t *req){
  char buf[10];
  int ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (ret <= 0) {
    return ESP_FAIL;
  }
  buf[ret] = '\0';
  Serial.printf("Comando recebido: %s\n", buf);
  if (strcmp(buf, "ON") == 0) {
    digitalWrite(OUTPUT_GPIO_NUM, HIGH);
    httpd_resp_send(req, "OUTPUT ON", HTTPD_RESP_USE_STRLEN);
  } else if (strcmp(buf, "OFF") == 0) {
    digitalWrite(OUTPUT_GPIO_NUM, LOW);
    httpd_resp_send(req, "OUTPUT OFF", HTTPD_RESP_USE_STRLEN);
  } else {
    httpd_resp_send(req, "INVALID COMMAND", HTTPD_RESP_USE_STRLEN);
  }
  return ESP_OK;
}

// Manipulador para capturar uma única imagem
static esp_err_t capture_handler(httpd_req_t *req){
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Falha na captura da câmera");
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  res = httpd_resp_set_type(req, "image/jpeg");
  if(res == ESP_OK){
    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  }
  esp_camera_fb_return(fb);
  return res;
}

// Função para iniciar o servidor da câmera
void startCameraServer(){
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  // URI para o streaming de vídeo
  httpd_uri_t index_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  // URI para controlar a saída digital
  httpd_uri_t control_uri = {
    .uri       = "/control",
    .method    = HTTP_POST,
    .handler   = control_handler,
    .user_ctx  = NULL
  };

  // URI para capturar uma única imagem
  httpd_uri_t capture_uri = {
    .uri       = "/capture",
    .method    = HTTP_GET,
    .handler   = capture_handler,
    .user_ctx  = NULL
  };

  // Inicia o servidor HTTP
  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &index_uri);
    httpd_register_uri_handler(stream_httpd, &control_uri);
    httpd_register_uri_handler(stream_httpd, &capture_uri); // Registra o novo endpoint
  }
}

void setup() {
  // Desativa o detector de brownout para evitar reinicializações indesejadas
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.setDebugOutput(false);

  // Configura o pino da saída digital como saída
  pinMode(OUTPUT_GPIO_NUM, OUTPUT);
  digitalWrite(OUTPUT_GPIO_NUM, LOW); // Inicialmente desligado

  // Configurações da câmera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG; 

  // Tamanho do frame e qualidade da imagem
  config.frame_size = FRAMESIZE_FHD; // 2048x1536
  config.jpeg_quality = 12;
  config.fb_count = 2;

  // Inicializa a câmera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Falha ao inicializar a câmera com erro 0x%x", err);
    return;
  }

  // Conecta-se ao Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Conectando-se ao WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi conectado");

  Serial.print("Acesse o streaming em: http://");
  Serial.println(WiFi.localIP());

  // Inicia o servidor da câmera
  startCameraServer();
}

void loop() {
  delay(1);  // Nenhuma ação relevante é realizada no loop
}
