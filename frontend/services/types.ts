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

export type WaterState = { count: number; goal: number };

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

export type GoalTimeframe = "none" | "quarterly" | "long_term";

export type VisionImage = {
  id: string;
  image: string;
  caption: string | null;
  created_at: string;
};

export type Goal = {
  id: string;
  title: string;
  category: "money" | "wellness" | "career" | "personal";
  target: string;
  deadline: string | null;
  emoji: string;
  timeframe: GoalTimeframe;
  progress: number;
  milestones: Milestone[];
  vision_images: VisionImage[];
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

export type CustomAffirmation = { id: string; text: string };

export type AffirmationState = {
  type: "morning" | "night";
  daily_affirmation: string;
  manifestation_prompt: string;
  custom: CustomAffirmation[];
  journal_entry: string;
};
