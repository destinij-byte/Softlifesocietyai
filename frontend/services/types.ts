export type User = {
  id: string;
  name: string;
  email: string;
  avatar_emoji: string;
  trial_started_at: string;
  trial_ends_at: string;
  subscription_status: "trialing" | "active" | "expired" | "canceled";
  subscription_tier: string | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type ChatMessage = {
  role: "user" | "luna";
  content: string;
  created_at: string;
};

export type FoodEntry = {
  id: string;
  name: string;
  calories: number;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  emoji: string;
  logged_at: string;
};

export type DailySummary = {
  date: string;
  total_calories: number;
  goal_calories: number;
  entries: FoodEntry[];
};

export type Workout = {
  id: string;
  name: string;
  workout_type: string;
  duration_minutes: number;
  emoji: string;
  notes: string | null;
  logged_at: string;
};

export type MealPlan = {
  id: string;
  title: string;
  emoji: string;
  description: string;
  days: number;
  meals: Record<string, string>;
};

export type Challenge = {
  slug: string;
  title: string;
  emoji: string;
  description: string;
  duration_days: number;
  joined: boolean;
  completed: boolean;
  participant_count: number;
};

export type Friend = {
  id: string;
  name: string;
  avatar_emoji: string;
  moved_today: boolean;
  recent_activity_count: number;
};
