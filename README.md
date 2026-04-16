1. Open Terminal and Activate Virtual Environment
Since you are on Windows and have a venv directory in your project, activate the virtual environment using PowerShell or Command Prompt.

For PowerShell:

powershell
.\venv\Scripts\Activate.ps1
For Command Prompt:

cmd
.\venv\Scripts\activate.bat
(You should see (venv) appear at the beginning of your terminal prompt indicating it's active.)

2. Install Dependencies (Optional but Recommended)
If you haven't recently installed the packages, ensure everything from requirements.txt is installed:

powershell
pip install -r requirements.txt
3. Run Database Migrations (If Needed)
If there have been recent updates to the database models, apply migrations. If everything is up to date, this won't hurt to run:

powershell
python manage.py migrate
4. Start the Development Server
Finally, run the project:

powershell
python manage.py runserver
Once the server starts running, it will output a local URL (typically http://127.0.0.1:8000/). You can open that address in your web browser to view your Smart Parking Application.

To stop the server at any time, press Ctrl + C in the terminal.

