"use client"

import { useEffect } from "react"
import { CallbackScreen } from "@/components/voice-loop/callback-screen"

export default function CallbackPage() {
    useEffect(() => {
        const searchParams = new URLSearchParams(window.location.search)
        const code = searchParams.get("code")

        if (code) {
            // Forward the code to the backend to exchange for a token
            // The backend will then redirect back to /?token=...
            window.location.href = `http://localhost:5000/auth/github/callback?code=${code}`
        } else {
            // If no code, go back to login
            window.location.href = "/"
        }
    }, [])

    return <CallbackScreen />
}
