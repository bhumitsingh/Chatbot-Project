'use client';
import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";

export const ChatBox = ({ messages }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="flex flex-col p-4 overflow-y-auto h-[75vh] border rounded-xl shadow-sm bg-gray-50">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          Start a conversation!
        </div>
      ) : (
        messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} message={msg.content} />
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
};