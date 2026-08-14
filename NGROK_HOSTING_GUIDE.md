# How to Host Your Project for the Defense Using Ngrok

If your supervisor asks to test the system live on their phone or laptop during your defense, **Ngrok** is the safest and easiest way to give them a public link. 

Instead of dealing with complicated cloud servers where uploaded files might get deleted, Ngrok creates a secure "tunnel" straight to your laptop. This means the system runs locally on your machine, but anyone with the link can access it anywhere in the world!

---

## Step 1: Download & Install Ngrok
1. Go to [ngrok.com](https://ngrok.com/) and create a free account.
2. Download the Ngrok software for Windows.
3. Extract (unzip) the downloaded file. You will get a single file called `ngrok.exe`. You can place this file anywhere (e.g., on your Desktop or inside your project folder).

## Step 2: Connect your Account (One-time setup)
You only need to do this step once to link the software to your free account.
1. Log into your Ngrok dashboard on their website.
2. Find your **Authtoken** (it will look like a long string of random letters and numbers).
3. Open your Command Prompt (`cmd`) or PowerShell in the folder where you put `ngrok.exe`.
4. Run the following command:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```
   *(Make sure to replace `YOUR_TOKEN_HERE` with your actual token).*

## Step 3: On the Day of the Defense
When it is time for your presentation, follow these exact steps:

1. **Start Your App Normally:** 
   Make sure your PostgreSQL database is running, and start the clearance system exactly like you normally do by running:
   ```bash
   python run.py
   ```
   *Your system should now be running locally at `http://localhost:5000`.*

2. **Start Ngrok:**
   Open a **new, separate** Command Prompt window (do not close the Python one!). Navigate to where your `ngrok.exe` is and run this command:
   ```bash
   ngrok http 5000
   ```

3. **Get Your Public Link:**
   Ngrok will start running and will display a public "Forwarding" URL that looks something like this:
   `https://a1b2c3d4.ngrok-free.app`

## That's it! 🎉
You can now write that `https://...ngrok-free.app` link on the whiteboard or send it to your supervisor. 
* They can open it on their phone or laptop. 
* Whatever they do on that website will be processed directly on your laptop.
* All receipts they upload will safely save to your local `/uploads` folder. 

When the defense is over, just close the Command Prompt window running Ngrok, and the public link will securely vanish.
