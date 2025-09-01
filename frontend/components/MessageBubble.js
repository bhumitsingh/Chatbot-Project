'use client';
import React from 'react';

export const MessageBubble = ({ role, message }) => {
  const isUser = role === "user";
  
  return (
    <div
      className={`rounded-2xl p-3 my-2 max-w-[75%] whitespace-pre-wrap transition-all duration-300 ${
        isUser 
          ? "bg-blue-100 ml-auto text-right border-l-4 border-blue-500" 
          : "bg-gray-200 mr-auto border-l-4 border-gray-500"
      }`}
    >
      <div className="text-sm font-medium mb-1 text-gray-600">
        {isUser ? "You" : "🤖 AI"}
      </div>
      <div className="text-gray-800">
        {message}
      </div>
    </div>
  );
};