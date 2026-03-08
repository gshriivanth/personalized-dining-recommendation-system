// hooks/useExploreRecommendations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchExploreRecommendations } from "@/lib/api/explore";
import { useProfileStore } from "@/lib/store/profile";
import type { ExploreRecommendResponse } from "@/lib/types/api";

export function useExploreRecommendations(query?: string, mealType?: string) {
  const { userId, goals, consumedToday } = useProfileStore();

  return useQuery<ExploreRecommendResponse, Error>({
    queryKey: ["explore-recommendations", query, mealType, consumedToday],
    queryFn: () =>
      fetchExploreRecommendations({
        user_id: userId ?? undefined,
        query,
        meal_type: mealType,
        goals,
        consumed_today: consumedToday,
        favorites: [],
        top_k: 10,
      }),
    // USDA data rarely changes — cache for 1 hour
    staleTime: 60 * 60 * 1000,
    enabled: true,
  });
}
