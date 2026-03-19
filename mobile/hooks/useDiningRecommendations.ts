// hooks/useDiningRecommendations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchDiningRecommendations } from "@/lib/api/dining";
import { useProfileStore } from "@/lib/store/profile";
import type { DiningRecommendResponse } from "@/lib/types/api";

export function useDiningRecommendations(
  hall: string,
  mealPeriod?: string
) {
  const { userId, goals, consumedToday, favorites } = useProfileStore();
  const favoriteIds = Array.from(favorites)
    .map((id) => parseInt(id.split(":")[1], 10))
    .filter((n) => !isNaN(n));

  return useQuery<DiningRecommendResponse, Error>({
    queryKey: ["dining-recommendations", hall, mealPeriod, consumedToday, favoriteIds],
    queryFn: () =>
      fetchDiningRecommendations({
        user_id: userId ?? undefined,
        hall,
        meal_period: mealPeriod,
        goals,
        consumed_today: consumedToday,
        favorites: favoriteIds,
        top_k: 8,
      }),
    // Dining menus change at meal period boundaries — stale after 15 min
    staleTime: 15 * 60 * 1000,
    enabled: !!hall,
  });
}
