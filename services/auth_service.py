from fastapi import HTTPException
from services.supabase_client import supabase
from supabase_auth.errors import AuthApiError
from postgrest.exceptions import APIError
import requests

class AuthService:

    @staticmethod
    def register(email: str, password: str, phone: str, full_name: str | None):
        # Step 1: Sign up
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
        except AuthApiError as e:
            msg = str(e)
            if "already registered" in msg.lower():
                raise HTTPException(status_code=400, detail="Email already registered")
            raise HTTPException(status_code=400, detail=msg)

        user = res.user
        if user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        user_id = user.id

        # Step 2: Insert profile
        try:
            supabase.table("profiles").insert({
                "id": user_id,
                "email": email,
                "phone": phone,
                "full_name": full_name,
                "notebook_id": None
            }).execute()
        except (APIError, AuthApiError) as e:
            # rollback user nếu tạo profile thất bại
            try:
                supabase.auth.admin.delete_user(user_id)
            except AuthApiError as rollback_err:
                # Nếu rollback thất bại, log nhưng không crash
                print(f"Rollback failed: {rollback_err}")
            raise HTTPException(status_code=400, detail="Failed to sign up. Email may already exist.")

        # Step 3: Create notebook if notebook_id is null
        profile = supabase.table("profiles") \
            .select("notebook_id") \
            .eq("id", user_id) \
            .single() \
            .execute() \
            .data

        if profile["notebook_id"] is None:
            resp = requests.post(
                "https://warnings-radius-considerations-exclusively.trycloudflare.com/api/notebooks",
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "name": full_name or email,
                    "description": ""
                }
            )

            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to create notebook")

            notebook_id = resp.json()["id"]

            supabase.table("profiles").update({
                "notebook_id": notebook_id
            }).eq("id", user_id).execute()

        return {
            "id": user_id,
            "email": email,
            "phone": phone,
            "full_name": full_name,
            "notebook_id": notebook_id
        }

    @staticmethod
    def login(email: str, password: str):
       
        try:
            res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
            })
        except AuthApiError as e:
            msg = str(e)
            if "invalid login credentials" in msg.lower():
                raise HTTPException(status_code=400, detail="Invalid email or password")
            raise HTTPException(status_code=400, detail=msg)
        
        if res.user is None:
            raise HTTPException(status_code=400, detail="Login failed")

        profile = supabase.table("profiles") \
            .select("notebook_id") \
            .eq("id", res.user.id) \
            .single() \
            .execute() \
            .data

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "notebook_id": profile["notebook_id"]
            }
        }

