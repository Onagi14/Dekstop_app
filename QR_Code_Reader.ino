#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>  // Include the LCD library

const char* WIFI_SSID = "Iyaah16";
const char* WIFI_PASS = "Aaa@060716";

WebServer server(80);

// LCD display settings
LiquidCrystal_I2C lcd(0x27, 16, 2);  // LCD I2C address is usually 0x27, 16 columns and 2 rows

// Define resolution levels for better performance
static auto loRes = esp32cam::Resolution::find(160, 120);
static auto midRes = esp32cam::Resolution::find(320, 240);
static auto hiRes = esp32cam::Resolution::find(640, 480);

QueueHandle_t lcdQueue;  // Create a queue for inter-task communication

void serveJpg() {
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}

void handleJpgLo() {
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}

void handleJpgHi() {
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}

void handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}

void handleDisplaySuccess() {
  lcd.clear();                // Clear the LCD screen
  lcd.setCursor(0, 0);        // Set cursor to the top-left corner
  lcd.print("Scanned Ok!");  // Display success message

  Serial.println("Scanned Ok!");  // Print to Serial Monitor
  server.send(200, "text/plain", "Success message displayed");
}

// Task for updating the LCD display
void lcdTask(void* pvParameters) {
  while (true) {
    String message = "";  // Placeholder for message from QR scan task
    if (xQueueReceive(lcdQueue, &message, portMAX_DELAY) == pdTRUE) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(message);
      Serial.println(message);  // Debugging print
    }
    vTaskDelay(500 / portTICK_PERIOD_MS);  // Task delay to prevent hogging CPU
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  // Initialize I2C with custom SDA (GPIO 15) and SCL (GPIO 14)
  Wire.begin(14, 15);  // SDA -> GPIO 15, SCL -> GPIO 14

  // Initialize the LCD display with I2C address 0x27
  lcd.begin(16, 2);  // 16 columns and 2 rows
  lcd.backlight();   // Turn on the LCD backlight
  lcd.setCursor(0, 0);  // Set cursor to the top-left
  lcd.print("Initializing...");
  delay(2000);  // Wait for 2 seconds to display the initialization message

  using namespace esp32cam;
  Config cfg;

  cfg.setPins(pins::AiThinker);
  cfg.setResolution(midRes);  // Start with mid resolution for a balance of speed and quality
  cfg.setBufferCount(1);
  cfg.setJpeg(60);

  bool ok = Camera.begin(cfg);
  Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    retries++;
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Connected to WiFi! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Failed to connect to WiFi.");
  }

  // Define routes
  server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-hi.jpg", handleJpgHi);
  server.on("/cam-mid.jpg", handleJpgMid);
  server.on("/display-success", HTTP_GET, handleDisplaySuccess);

  server.begin();

  // Initialize the queue
  lcdQueue = xQueueCreate(10, sizeof(String));  // Create a queue for passing messages to LCD task

  // Create the LCD task
  xTaskCreate(lcdTask, "LCD Task", 2048, NULL, 1, NULL);
}

void loop() {
  server.handleClient();

  // Simulate QR code detection (replace with actual QR data fetching logic)
  String data = "";  // Replace with actual QR data fetching logic

  static bool isWaiting = true;               // Track whether we're waiting for QR code
  static unsigned long lastDisplayTime = 0;   // Last time display was updated
  static unsigned long lastScanTime = 0;      // Last time scan was successful
  const unsigned long scanDelay = 5000;       // 5 seconds to show "Scanned Successfully"
  const unsigned long waitDelay = 3000;       // 3 seconds to show "Waiting for QR Code"
  static unsigned long lastWaitUpdateTime = 0; // Track time of last "waiting" update
  static byte waitingDots = 0;                // Counter for dots in waiting message

  // If QR code data is detected (ensure 'data' contains the QR code value)
  if (data != "") {
    if (millis() - lastScanTime > scanDelay) {  // Only update after delay
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Scanned OK!");
      
      Serial.println("Scanned Successfully!");
      lastScanTime = millis();  // Update the last scan time

      // Set flag to avoid redundant "Waiting for QR Code" messages
      isWaiting = false;
      lastDisplayTime = millis();  // Record the time of display change
    }
  } 
  else if (millis() - lastDisplayTime > waitDelay && isWaiting) {
    // Show "Waiting for QR Code" with changing dots animation
    if (millis() - lastWaitUpdateTime > 1000) {  // Update every 1 second
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Waiting");

      // Create a string with the correct number of dots
      String waitingMessage = "Waiting";
      String dots = "";  // Temporary string to store dots

      // Add the correct number of dots based on waitingDots
      for (byte i = 0; i < waitingDots; i++) {
        dots += ".";
      }

      // Concatenate dots to the "Waiting" message
      waitingMessage += dots;

      // Convert to const char* for the queue
      const char* msg = waitingMessage.c_str(); 

      // Send the message to the queue
      xQueueSendToBack(lcdQueue, (const void*)msg, portMAX_DELAY); 

      waitingDots = (waitingDots + 1) % 4;  // Cycle through 0 to 3 dots

      Serial.println("Waiting for QR Code...");
      lastWaitUpdateTime = millis();  // Update last wait update time
      lastDisplayTime = millis();  // Update last display time
    }
  }

  // Debugging: Check if data is being set correctly (you can add more debugging here)
  Serial.println(data); // This should show the QR code data if detected
}
