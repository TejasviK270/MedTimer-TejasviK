# MedTimer-TejasviK


Candidate Name: Tejasvi Reddy Kandimalla

Candidate Registration Number-: 1000467 

CRS Name: Artificial Intelligence 

Course Name:  Unit 2- Design and Deploy Interactive Python Applicaitons for Social Good

School Name: Birla Open Minds International School, Kollur 


Link to Live App: https://medtimer-tejasvik-btkjxqkxt5un6muund5wdd.streamlit.app/

**Project Overvview**

MedTimer is a personalized daily medicine companion designed to help users manage their medication schedules with ease and consistency. Built using Streamlit, the app allows users to add recurring medicine schedules or one-off doses, track their daily adherence, and receive automatic audio reminders when it’s time to take their medicine. The interface is simple and intuitive, featuring large fonts, soft colors, and a three-column layout that separates input, checklist, and insights. Users can view a color-coded checklist (green for taken, yellow for upcoming, red for missed), monitor their weekly adherence score, and enjoy motivational tips and celebratory Turtle graphics when they stay consistent. MedTimer is ideal for individuals, caregivers, or families looking for a gentle, reliable way to stay on top of daily health routines.

**Key Features**

MedTimer is designed to make medicine management simple, reliable, and encouraging. Its key features include:

- Hybrid medicine input: Add medicines either by selecting from a dropdown of common options or typing custom names manually.
  
- Recurring schedules: Create flexible schedules with multiple doses per day and across selected days of the week.
  
- One‑off doses: Quickly add a single medicine dose for today without setting up a full schedule.
  
- Color‑coded checklist: View your daily medicines with clear status indicators — green for taken, yellow for upcoming, and red for missed.
  
- Automatic audio reminders: Hear a gentle beep when a dose is due within your chosen reminder window, so you never miss a medicine.
  
- Weekly calendar view: See all scheduled doses for the week in a simple table format, making planning easier.
  
- Adherence tracking: Monitor your weekly adherence score, calculated from scheduled versus taken doses.
  
- Celebratory visuals: Enjoy Turtle graphics trophies when you maintain high adherence (desktop only).
  
- Motivational tips: Receive encouraging messages to help you stay consistent and positive about your health routine.
  
- Safe state management: Built with Streamlit’s session_state to ensure smooth updates, safe reruns, and reliable tracking across sessions.
  
- Clean, accessible design: Large fonts, soft colors, and a three‑column layout make the app easy to use for all ages.


**Integration Details**

MedTimer is built entirely in Python using the Streamlit framework, which enables real-time interactivity and a clean web-based interface. The app uses Python’s built-in datetime module for scheduling logic, session_state for persistent tracking of medicine schedules and adherence, and the struct and math libraries to generate custom WAV audio alerts. Turtle graphics are used to display celebratory visuals for users who maintain high adherence, though these open in a separate window and are best experienced on desktop. The app supports hybrid medicine input—users can either select from a dropdown of common medicines or enter custom names manually. It also supports multiple doses per day, flexible start dates, and recurring schedules across selected days of the week. All reminders are handled within the app session, with automatic audio beeps triggered when a dose is due within the user-defined reminder window.

**Deployment Instructions**

To deploy MedTimer locally, first clone the repository from GitHub and navigate into the project directory. Install the required dependencies using the provided requirements.txt file, which includes Streamlit and any necessary Python libraries. Once installed, launch the app by running streamlit run app.py from your terminal. This will open the app in your default browser.
For cloud deployment, push the code to a public GitHub repository and head to Streamlit Cloud. Create a new app, connect your GitHub account, and select the repository and app.py file as the entry point. Streamlit Cloud will automatically install dependencies and deploy the app. Note that Turtle graphics may not render on cloud platforms, and audio reminders work best in browsers that support autoplay for short WAV files. For optimal performance, users should keep the app open during the day to receive timely reminders and track their progress.

