import React from "react";
import { Users, User as UserIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { User } from "../types";

interface SidebarProps {
  user: User;
  isOpen: boolean;
  onToggle: () => void;
  customers: any[];
  onSelectCustomer: (customerId: string) => void;
  onResetView: () => void;
}

export default function Sidebar({
  user,
  isOpen,
  onToggle,
  customers,
  onSelectCustomer,
  onResetView,
}: SidebarProps) {
  return (
    <div
      className={`relative flex flex-col bg-white dark:bg-zinc-900 border-r border-gray-200 dark:border-zinc-800 transition-all duration-300 ease-in-out ${
        isOpen ? "w-72" : "w-0"
      } h-full`}
    >
      <button
        onClick={onToggle}
        className={`absolute top-4 -right-10 z-20 p-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-r-xl shadow-sm text-gray-500 hover:text-teal-600 transition-colors cursor-pointer ${
          !isOpen && "opacity-100"
        }`}
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      <div className={`flex flex-col h-full overflow-hidden ${isOpen ? "opacity-100" : "opacity-0 invisible"} transition-opacity duration-300 delay-100`}>
        
        <div 
          className="p-4 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between shrink-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
          onClick={onResetView}
        >
          <h2 className="text-sm font-semibold text-gray-800 dark:text-zinc-200 flex items-center gap-2">
            <Users size={16} className="text-teal-500" />
            Customer Delight
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1 custom-scrollbar">
          {/* Customer list removed as it is now shown in the main table */}
        </div>
      </div>
    </div>
  );
}
