"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Mic, Github, Zap, Car, Code2 } from "lucide-react"

interface LoginScreenProps {
  onLogin: () => void
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-success/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <Badge variant="secondary" className="bg-success/10 text-success border-success/20 px-4 py-1.5">
            <span className="relative flex h-2 w-2 mr-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
            </span>
            System Online
          </Badge>

          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-balance">
            <span className="text-foreground">Voice</span>
            <span className="text-accent">Loop</span>
          </h1>

          <p className="text-xl text-muted-foreground font-medium tracking-wide">
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

            {/* Features */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <FeatureItem icon={Mic} label="Voice Control" />
              <FeatureItem icon={Car} label="Hands-Free" />
              <FeatureItem icon={Code2} label="AI Powered" />
            </div>
          </CardContent>
        </Card>

        {/* Tech Badges */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <TechBadge icon={Zap} label="Gemini AI" />
          <TechBadge icon={Mic} label="ElevenLabs" />
          <TechBadge icon={Github} label="GitHub API" />
        </div>
      </div>
    </main>
  )
}

function FeatureItem({ icon: Icon, label }: { icon: typeof Mic; label: string }) {
  return (
    <div className="flex flex-col items-center gap-2 p-3 rounded-xl bg-secondary/30 border border-border/50">
      <div className="p-2 rounded-lg bg-accent/10">
        <Icon className="h-5 w-5 text-accent" />
      </div>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  )
}

function TechBadge({ icon: Icon, label }: { icon: typeof Mic; label: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50">
      <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  )
}
