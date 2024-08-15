import React from "react";
import ReactMarkdown from "react-markdown";

const MarkdownRenderer = ({ index, content, className }) => {
  if (content.trim() === "") {
    // add new line
    return <br />;
  }

  return (
    <div key={index} className={`prose ${className}`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
