Deploying to Vercel

1) Prereqs
   - Install Vercel CLI:
     - npm i -g vercel
   - Login:
     - vercel login

2) Deploy (from this folder)
   - cd /Users/harig/Desktop/dos_vercel_app
   - vercel --prod

Notes
- This is a static site. Your app is fully client-side and mirrors the original HTML (Plotly + JS).
- If you want to regenerate the HTML in future, run your Python script locally and overwrite index.html.
- Optionally, you can rename the project on Vercel after the first deploy.


