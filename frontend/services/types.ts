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

export type LunaAction = {
  type: string;
  label: string;
  payload: Record<string, unknown>;
};

export type ChatMessage = {
  id?: string;
  role: "user" | "luna";
  content: string;
  mode: LunaMode;
  actions?: LunaAction[];
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

export type BreakdownItem = { id: string; period: "monthly" | "weekly" | "today"; label: string; target: number | null; done: boolean };

export type Goal = {
  id: string;
  title: string;
  category: "money" | "wellness" | "career" | "personal";
  target: string;
  deadline: string | null;
  emoji: string;
  timeframe: GoalTimeframe;
  pillar: Pillar | null;
  why: string | null;
  target_value: number | null;
  progress: number;
  milestones: Milestone[];
  vision_images: VisionImage[];
  breakdown: BreakdownItem[];
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

export type Pillar = "mind" | "body" | "glow" | "money" | "career" | "home" | "relationships" | "growth";

export type Era = "glow_up" | "wellness" | "money" | "ceo" | "discipline" | "peace" | "new" | "soft_life";

export type CatalogEntry = { label: string; emoji: string };

export type PillarPriority = { pillar: Pillar; priority: number };

export type CoachingStyle = "gentle" | "direct" | "tough_love" | "cheerleader";
export type MotivationStyle = "accountability" | "encouragement" | "results" | "big_picture";
export type DietaryStyle = "none" | "vegetarian" | "vegan" | "pescatarian" | "gluten_free" | "dairy_free" | "low_carb";

export type NutritionPreferences = {
  dietary_style: DietaryStyle | null;
  notes: string;
};

export type Blueprint = {
  era: Era | null;
  current_state: string;
  becoming: string;
  pillars: PillarPriority[];
  preferred_name: string | null;
  coaching_style: CoachingStyle | null;
  motivation_style: MotivationStyle | null;
  affirmation_categories: string[];
  manifestation_categories: string[];
  nutrition_preferences: NutritionPreferences;
  created_at?: string;
  updated_at?: string;
};

export type HomeContext = {
  era: Era | null;
  era_label: string | null;
  becoming: string;
  top_pillars: { pillar: Pillar; label: string; emoji: string }[];
  yesterday_focus: string | null;
};

export type DaySnapshot = {
  log_date: string;
  calories_logged: number;
  calories_goal: number;
  water_count: number;
  water_goal: number;
  ritual_done: number;
  ritual_total: number;
  mood: string | null;
};

export type NightCheckin = {
  log_date: string;
  completed: boolean;
  win: string;
  gratitude: string;
  tomorrow_focus: string;
  day_summary: DaySnapshot;
};

export type PillarAlignment = { pillar: Pillar; label: string; score: number };

export type Alignment = {
  score: number;
  why: string;
  pillar_scores: PillarAlignment[];
};

export type ChallengeWeek = { slug: string; title: string; emoji: string; check_ins_this_week: number };

export type GoalOverview = { title: string; pillar: Pillar | null; progress: number };

export type WeeklyReset = {
  week_start: string;
  week_end: string;
  days: DaySnapshot[];
  water_avg_pct: number;
  nourish_days_logged: number;
  mood_days_logged: number;
  checkins_completed: number;
  best_day: string | null;
  challenges: ChallengeWeek[];
  goals_overview: GoalOverview[];
  alignment: Alignment;
};

export type CustomAffirmation = { id: string; text: string };

export type AffirmationState = {
  type: "morning" | "night";
  daily_affirmation: string;
  daily_affirmation_id: string;
  daily_affirmation_category: string | null;
  daily_affirmation_favorited: boolean;
  manifestation_prompt: string;
  custom: CustomAffirmation[];
  journal_entry: string;
};

export type AffirmationHistoryEntry = {
  id: string;
  text: string;
  category: string | null;
  favorited: boolean;
  created_at: string;
};
