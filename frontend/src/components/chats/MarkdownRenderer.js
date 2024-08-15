import React from "react";
import ReactMarkdown from "react-markdown";

const MarkdownRenderer = ({ content, className }) => {
  if (content.trim() === "") {
    // add new line
    return <br />;
  }

  return (
    <div className={`prose ${className}`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
