import { useState } from "react";

export default function useAICaption() {
  const [suggestions, setSuggestions] =
    useState([]);

  const [selectedSuggestion, setSelectedSuggestion] =
    useState(null);

  function clearSuggestions() {
    setSuggestions([]);
    setSelectedSuggestion(null);
  }

  return {
    suggestions,
    setSuggestions,

    selectedSuggestion,
    setSelectedSuggestion,

    clearSuggestions,
  };
}