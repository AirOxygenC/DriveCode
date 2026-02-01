"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Github } from "lucide-react"

interface LoginScreenProps {
  onLogin: () => void
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-start pt-12 p-4 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-success/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-lg space-y-3">
        {/* Header */}
        <div className="text-center space-y-2">
          {/* DriveCode Logo - Extra Large */}
          <div className="flex justify-center py-2">
            <img
              src="/DriveCodelogo.png"
              alt="DriveCode Logo"
              className="h-64 md:h-80 w-auto object-contain"
            />
          </div>

          <p className="text-xl text-green-500 font-medium tracking-wide">
            Drive. Speak. Ship.
          </p>
        </div>

        {/* Main Card */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50 shadow-2xl">
          <CardContent className="p-8 space-y-6">
            <div className="space-y-4 text-center">
              <p className="text-muted-foreground leading-relaxed">
                Transform your ideas into code while driving. Voice Loop uses AI to turn your spoken thoughts into production-ready code, safely committed to GitHub.
              </p>
            </div>

            <Button
              size="lg"
              className="w-full h-14 text-lg font-semibold bg-foreground text-background hover:bg-foreground/90 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
              onClick={onLogin}
            >
              <Github className="mr-3 h-5 w-5" />
              Login with GitHub
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
