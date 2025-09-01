'use client';
import { useEffect, useState } from "react";
import { ChatBox } from "@/components/ChatBox";
import MessageInput from "@/components/MessageInput";
import { ModelSelector } from "@/components/ModelSelector";
import { sendMessageToBackend } from "@/utils/api";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [model, setModel] = useState("open_llama");

  useEffect(() => {
    const stored = localStorage.getItem("chat_history");
    if (stored) {
      try {
        setMessages(JSON.parse(stored));
      } catch (error) {
        console.error("Error parsing stored messages:", error);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("chat_history", JSON.stringify(messages));
  }, [messages]);

  const sendMessage = async (input) => {
    if (!input.trim()) return;
    
    console.log("Sending message:", input, "with model:", model);
    
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await sendMessageToBackend(input, model);
      console.log("Received response:", res);
      
      const aiMsg = { role: "ai", content: res.response || "⚠️ No reply" };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMsg = { role: "ai", content: "⚠️ Error sending message" };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem("chat_history");
  };

  return (
    <main className="max-w-3xl mx-auto py-4 px-2">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Chat UI</h1>
        <button
          onClick={clearChat}
          className="bg-red-500 text-white px-3 py-1 rounded-md hover:bg-red-600 text-sm"
        >
          Clear Chat
        </button>
      </div>
      <ModelSelector selected={model} setSelected={setModel} />
      <ChatBox messages={messages} />
      <MessageInput onSend={sendMessage} />
    </main>
  );
}