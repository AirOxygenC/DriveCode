"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Shield, CheckCircle2, Fingerprint } from "lucide-react"

const LOADING_MESSAGES = [
  { text: "Scanning Identity...", icon: Fingerprint },
  { text: "Handshaking with Headquarters...", icon: Shield },
  { text: "Access Granted", icon: CheckCircle2 },
]

export function CallbackScreen() {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < LOADING_MESSAGES.length - 1) {
          return prev + 1
        }
        clearInterval(timer)
        return prev
      })
    }, 800)

    return () => clearInterval(timer)
  }, [])

  const CurrentIcon = LOADING_MESSAGES[currentStep].icon

  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-success/10 rounded-full blur-3xl animate-pulse" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        <Card className="bg-card/50 backdrop-blur-xl border-border/50 shadow-2xl">
          <CardContent className="p-8 space-y-6">
            <Badge variant="secondary" className="bg-accent/10 text-accent border-accent/20 px-4 py-1.5 mx-auto flex w-fit">
              <span className="relative flex h-2 w-2 mr-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
              </span>
              Uplink Active
            </Badge>

            <div className="text-center space-y-6">
              <div className="relative mx-auto w-20 h-20">
                <div className="absolute inset-0 rounded-full bg-accent/20 animate-ping" />
                <div className="relative flex items-center justify-center w-20 h-20 rounded-full bg-secondary border border-border">
                  <CurrentIcon className="h-8 w-8 text-accent" />
                </div>
              </div>

              <h1 className="text-2xl font-bold text-foreground">
                {LOADING_MESSAGES[currentStep].text}
              </h1>

              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 text-accent animate-spin" />
                <span className="text-sm text-muted-foreground">Establishing secure connection...</span>
              </div>

              {/* Progress Steps */}
              <div className="flex justify-center gap-2 pt-4">
                {LOADING_MESSAGES.map((_, index) => (
                  <div
                    key={index}
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      index <= currentStep
                        ? "w-8 bg-accent"
                        : "w-2 bg-border"
                    }`}
                  />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
