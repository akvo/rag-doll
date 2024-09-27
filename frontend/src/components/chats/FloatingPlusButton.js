import { useState, useEffect, useRef } from "react";
import { PlusIcon, CloseIcon } from "@/utils/icons";

const FloatingPlusButton = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    // Close the menu when clicking outside
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative">
      {/* Floating Button */}
      <button
        className={`fixed bottom-24 right-5 p-3 rounded-xl shadow-lg ${
          isOpen
            ? "bg-gray-300"
            : "bg-akvo-green hover:bg-green-700 transition duration-300 ease-in-out"
        }`}
        onClick={toggleMenu}
      >
        {isOpen ? <CloseIcon /> : <PlusIcon />}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          ref={menuRef}
          className="fixed bottom-36 right-5 bg-white rounded-lg shadow-md shadow-slate-300 border p-4 w-56 mb-4"
        >
          <ul>
            <li
              className="text-black hover:text-akvo-green cursor-pointer"
              onClick={() => {
                console.log("Add Farmer clicked");
                setIsOpen(false);
              }}
            >
              Add Farmer
              <div className="text-xs text-gray-500 border-t border-t-gray-500 pt-1 mt-1">
                Onboarding farmer to the platform
              </div>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default FloatingPlusButton;
