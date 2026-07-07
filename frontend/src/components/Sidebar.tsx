import React, { useEffect, useState } from "react";
import { Users, User as UserIcon, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { User } from "../types";

interface SidebarProps {
  user: User;
  isOpen: boolean;
  onToggle: () => void;
  onSelectCustomer: (customerId: string) => void;
}

export default function Sidebar({
  user,
  isOpen,
  onToggle,
  onSelectCustomer,
}: SidebarProps) {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && isOpen) {
      fetchCustomers();
    }
  }, [user, isOpen]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/customers`);
      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch (err) {
      console.error("Failed to fetch customers:", err);
    } finally {
      setLoading(false);
    }
  };

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
        
        <div className="p-4 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between shrink-0">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-zinc-200 flex items-center gap-2">
            <Users size={16} className="text-teal-500" />
            Customer Directory
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1 custom-scrollbar">
          {loading && customers.length === 0 ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="animate-spin text-teal-500" size={24} />
            </div>
          ) : customers.length === 0 ? (
            <div className="text-center py-8 text-xs text-gray-400">
              No customers found.
            </div>
          ) : (
            customers.map((customer) => (
              <div
                key={customer.customer_id}
                onClick={() => onSelectCustomer(customer.customer_id)}
                className="group relative w-full text-left p-3 rounded-xl transition-all flex flex-col gap-1 cursor-pointer bg-transparent border border-transparent hover:bg-gray-100 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-zinc-300"
              >
                <div className="flex items-start gap-2">
                  <UserIcon size={14} className="shrink-0 mt-0.5 text-gray-400 group-hover:text-teal-500" />
                  <span className="text-sm font-medium leading-tight">
                    {customer.customer_name || customer.customer_id}
                  </span>
                </div>
                <div className="flex justify-between items-center pl-6 pr-1 mt-1">
                  <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
                    {customer.account_type || "Standard"}
                  </span>
                  <span className="text-[10px] bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400 px-1.5 py-0.5 rounded-full font-bold">
                    Analyze
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
