from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Optional
import asyncio
import threading
import traceback
import time
import uvicorn

# Import your backend run script
from backend_run import instagram_login

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutomationRequest(BaseModel):
    username: str
    password: str
    reel_url: str
  

class AutomationController:
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.stop_event = threading.Event()
        self.automation_thread: Optional[threading.Thread] = None
        self.status = "idle"
        self.error_message = None
        self.last_run_time = 0

    def reset(self):
        """Reset the automation controller to its initial state"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.driver = None
        self.stop_event.clear()
        self.automation_thread = None
        self.status = "idle"
        self.error_message = None
        self.last_run_time = time.time()

    def run_automation(self, username: str, password: str, reel_url: str):
        try:
            self.status = "running"
            self.stop_event.clear()

            # Configure Chrome options
            chrome_options = Options()
            # chrome_options.add_argument("--headless")
            # chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Initialize the driver
            self.driver = webdriver.Chrome(options=chrome_options)

            # Run the Instagram login and automation
            instagram_login(
                username, 
                password, 
                reel_url, 
                stop_event=self.stop_event,
                driver=self.driver
            )

            if self.stop_event.is_set():
                self.status = "stopped"
            else:
                self.status = "completed"

        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            traceback.print_exc()

        finally:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.driver = None

    def start(self, username: str, password: str, reel_url: str):
        # Check if enough time has passed since the last run
        current_time = time.time()
        if current_time - self.last_run_time < 5:  # 5-second cooldown
            raise Exception("Please wait a few seconds before starting a new automation")

        # Check if a thread is already running
        if self.automation_thread and self.automation_thread.is_alive():
            raise Exception("Automation is already running")

        # Reset the controller state
        self.reset()

        # Start a new thread
        self.automation_thread = threading.Thread(
            target=self.run_automation, 
            args=(username, password, reel_url)
        )
        self.automation_thread.start()
        self.last_run_time = current_time

    def stop(self):
        if self.stop_event:
            self.stop_event.set()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.status = "stopped"

# Global automation controller
automation_controller = AutomationController()

@app.post("/start-automation")
async def start_automation(request: AutomationRequest):
    try:
        automation_controller.start(
            request.username, 
            request.password, 
            request.reel_url,
          
        )
        return {
            "status": "success", 
            "message": "Automation started"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stop-automation")
async def stop_automation():
    try:
        automation_controller.stop()
        return {
            "status": "success", 
            "message": "Automation stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/automation-status")
async def get_automation_status():
    return {
        "status": automation_controller.status,
        "error_message": automation_controller.error_message
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)