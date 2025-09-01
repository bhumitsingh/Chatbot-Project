'use client';
import React from 'react';

export const ModelSelector = ({ selected, setSelected }) => {
  const models = [
    { label: "🦙 Open LLaMA", value: "open_llama" },
    { label: "🧠 Mistral", value: "mistral" },
    { label: "🦾 Deepseek LLaMA 70B", value: "deepseek_llama70b" },
    { label: "💎 Gemini Flash", value: "gemini_flash" },
  ];

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select Model:
      </label>
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        className="w-full p-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        {models.map((model) => (
          <option key={model.value} value={model.value}>
            {model.label}
          </option>
        ))}
      </select>
    </div>
  );
};