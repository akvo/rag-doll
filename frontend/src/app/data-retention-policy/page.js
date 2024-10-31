"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib";

const DataRetentionPolicy = () => {
  const [content, setContent] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.get("/data-retention-policy");
      const resData = await response.json();
      setContent(resData);
    };
    fetchData();
  }, []);

  return (
    <div className="w-full mx-auto h-screen overflow-y-auto py-12 px-10">
      <h1 className="text-xl font-bold text-center text-akvo-green mb-6">
        Agriconnect Data Retention Policy
      </h1>
      {content.map((section, index) => (
        <div
          key={index}
          className="mb-8 p-4 bg-gray-100 rounded-lg shadow-inner"
        >
          <h2 className="text-lg font-semibold text-gray-700 mb-4 border-b border-gray-300 pb-2">
            {section.title}
          </h2>
          {section.sections.map((item, idx) => (
            <div key={idx} className="mb-4 p-3 bg-white rounded-lg shadow">
              <h3 className="text-base font-medium text-gray-800 mb-2">
                {item.subtitle}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {item.content}
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default DataRetentionPolicy;
