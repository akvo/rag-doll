import React from "react";
import ReactMarkdown from "react-markdown";

const MarkdownRenderer = ({ index, content, className }) => {
  return (
    <div key={index} className={`prose ${className}`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
