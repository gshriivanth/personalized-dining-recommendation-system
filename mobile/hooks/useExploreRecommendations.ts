// hooks/useExploreRecommendations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchExploreRecommendations } from "@/lib/api/explore";
import { useProfileStore } from "@/lib/store/profile";
import type { ExploreRecommendResponse } from "@/lib/types/api";

export function useExploreRecommendations(query?: string, mealType?: string) {
  const { userId, goals, consumedToday, favorites } = useProfileStore();

  // Convert compound IDs ("source:food_id") to numeric food_ids for the backend
  const favoriteIds = Array.from(favorites)
    .map((id) => parseInt(id.split(":")[1], 10))
    .filter((n) => !isNaN(n));

  // Only fetch if there's an active search query OR the user has non-dining favorites
  const hasNonDiningFavorites = Array.from(favorites).some(
    (id) => !id.startsWith("uci_dining_")
  );
  const enabled = !!query || hasNonDiningFavorites;

  return useQuery<ExploreRecommendResponse, Error>({
    queryKey: ["explore-recommendations", query, mealType, consumedToday, favoriteIds],
    queryFn: () =>
      fetchExploreRecommendations({
        user_id: userId ?? undefined,
        query,
        meal_type: mealType,
        goals,
        consumed_today: consumedToday,
        favorites: favoriteIds,
        top_k: 10,
      }),
    staleTime: 60 * 60 * 1000,
    enabled,
  });
}
