export type User = {
  id: string;
  name: string;
  email: string;
  avatar_emoji: string;
  trial_started_at: string;
  trial_ends_at: string;
  subscription_status: "trialing" | "active" | "free" | "expired" | "canceled";
  subscription_tier: string | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type LunaMode = "life" | "money" | "wellness" | "goals";

export type ChatMessage = {
  role: "user" | "luna";
  content: string;
  mode: LunaMode;
  created_at: string;
};

export type FoodEntry = {
  id: string;
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  emoji: string;
  logged_at: string;
};

export type DailySummary = {
  date: string;
  total_calories: number;
  goal_calories: number;
  total_protein_g: number;
  goal_protein_g: number;
  total_carbs_g: number;
  goal_carbs_g: number;
  total_fat_g: number;
  goal_fat_g: number;
  entries: FoodEntry[];
};

export type FoodResult = {
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  emoji: string;
};

export type MealSuggestion = FoodResult & {
  description?: string | null;
  note?: string | null;
};

export type Milestone = { id: string; title: string; done: boolean };

export type Goal = {
  id: string;
  title: string;
  category: "money" | "wellness" | "career" | "personal";
  target: string;
  deadline: string | null;
  emoji: string;
  progress: number;
  milestones: Milestone[];
  created_at: string;
};

export type RoutineStep = { id: string; label: string; done: boolean };

export type Routine = {
  type: "morning" | "night";
  steps: RoutineStep[];
};

export type ChallengeTemplate = {
  slug: string;
  title: string;
  emoji: string;
  duration_days: number;
  needs_intensity: boolean;
  description?: string;
};

export type MyChallenge = {
  slug: string;
  title: string;
  emoji: string;
  intensity: string | null;
  duration_days: number;
  day_count: number;
  streak: number;
  points: number;
  logged_today: boolean;
  progress: number;
};

export type LeaderboardRow = {
  id: string;
  name: string;
  avatar_emoji: string;
  points: number;
  streak: number;
  is_you: boolean;
  rank: number;
};

export type Friend = {
  id: string;
  name: string;
  avatar_emoji: string;
};
