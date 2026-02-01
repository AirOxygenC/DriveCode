"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Mic,
  LogOut,
  FolderGit2,
  Lock,
  Plus,
  Loader2,
  Code2,
  Calendar,
} from "lucide-react"

interface Repo {
  id: number
  name: string
  private: boolean
  language: string | null
  updated_at: string
}

interface DashboardProps {
  onSelectRepo: (repo: Repo) => void
  selectedRepo: Repo | null
  onStartCoding: () => void
  onSignOut: () => void
}

// Mock data for demonstration
const MOCK_REPOS: Repo[] = [
  { id: 1, name: "voice-loop-app", private: false, language: "TypeScript", updated_at: "2025-01-30T10:00:00Z" },
  { id: 2, name: "ai-assistant", private: true, language: "Python", updated_at: "2025-01-28T15:30:00Z" },
  { id: 3, name: "react-components", private: false, language: "JavaScript", updated_at: "2025-01-25T09:00:00Z" },
  { id: 4, name: "api-gateway", private: true, language: "Go", updated_at: "2025-01-20T12:00:00Z" },
  { id: 5, name: "mobile-app", private: false, language: "Swift", updated_at: "2025-01-18T16:45:00Z" },
  { id: 6, name: "data-pipeline", private: true, language: "Python", updated_at: "2025-01-15T08:30:00Z" },
]

const MOCK_USER = {
  login: "developer",
  avatar_url: "https://github.com/github.png",
}

export function Dashboard({ onSelectRepo, selectedRepo, onStartCoding, onSignOut }: DashboardProps) {
  const [loading] = useState(false)
  const repos = MOCK_REPOS
  const user = MOCK_USER

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  }

  return (
    <main className="min-h-screen bg-background flex flex-col items-center p-4 md:p-8 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-success/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-2xl space-y-6">
        {/* Header Card */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12 border-2 border-accent">
                  <AvatarImage src={user.avatar_url || "/placeholder.svg"} alt={user.login} />
                  <AvatarFallback className="bg-secondary text-foreground">
                    {user.login[0].toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold text-foreground">@{user.login}</p>
                  <Badge variant="secondary" className="bg-success/10 text-success border-success/20 text-xs">
                    Connected
                  </Badge>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onSignOut}
                className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* Main Content Card */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50 shadow-2xl">
          <CardContent className="p-6 md:p-8 space-y-6">
            <div className="text-center space-y-2">
              <h1 className="text-3xl md:text-4xl font-bold text-foreground">
                Welcome, Pilot.
              </h1>
              <p className="text-muted-foreground text-lg">
                Which repository are we coding in today?
              </p>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <Loader2 className="h-10 w-10 text-accent animate-spin" />
                <p className="text-muted-foreground">Loading your repositories...</p>
              </div>
            ) : (
              <ScrollArea className="h-[300px] pr-4">
                <div className="space-y-2">
                  {repos.map((repo) => (
                    <button
                      key={repo.id}
                      onClick={() => onSelectRepo(repo)}
                      className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all duration-200 text-left group ${
                        selectedRepo?.id === repo.id
                          ? "bg-accent/15 border-2 border-accent"
                          : "bg-secondary/30 border-2 border-transparent hover:bg-secondary/50 hover:border-border"
                      }`}
                    >
                      <div className={`p-2.5 rounded-lg ${
                        selectedRepo?.id === repo.id
                          ? "bg-accent/20"
                          : "bg-secondary group-hover:bg-secondary/80"
                      }`}>
                        {repo.private ? (
                          <Lock className={`h-5 w-5 ${
                            selectedRepo?.id === repo.id ? "text-accent" : "text-muted-foreground"
                          }`} />
                        ) : (
                          <FolderGit2 className={`h-5 w-5 ${
                            selectedRepo?.id === repo.id ? "text-accent" : "text-muted-foreground"
                          }`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`font-semibold truncate ${
                          selectedRepo?.id === repo.id ? "text-foreground" : "text-foreground"
                        }`}>
                          {repo.name}
                        </p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          {repo.language && (
                            <span className="flex items-center gap-1">
                              <Code2 className="h-3 w-3" />
                              {repo.language}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(repo.updated_at)}
                          </span>
                        </div>
                      </div>
                      {selectedRepo?.id === repo.id && (
                        <div className="w-2 h-2 rounded-full bg-accent" />
                      )}
                    </button>
                  ))}
                </div>
              </ScrollArea>
            )}

            {selectedRepo && (
              <Button
                size="lg"
                className="w-full h-14 text-lg font-semibold bg-accent text-accent-foreground hover:bg-accent/90 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-accent/25"
                onClick={onStartCoding}
              >
                <Mic className="mr-3 h-5 w-5" />
                Start Voice Coding
              </Button>
            )}

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-3 text-muted-foreground">or</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="lg"
              className="w-full h-14 text-base font-medium border-2 border-dashed border-border hover:border-success hover:text-success hover:bg-success/5 transition-all duration-200 bg-transparent"
            >
              <Plus className="mr-2 h-5 w-5" />
              Create a New Repository
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
