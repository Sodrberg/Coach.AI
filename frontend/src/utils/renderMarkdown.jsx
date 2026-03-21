/**
 * Lightweight markdown-to-JSX renderer for LLM-generated content.
 * Supports: # headings, ## headings, **bold**, - unordered lists, 1. ordered lists, paragraphs.
 */
export default function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Skip empty lines
    if (line.trim() === '') {
      i++;
      continue;
    }

    // ## Heading 3
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="text-base font-heading font-semibold text-text-primary mt-5 mb-2">
          {inlineParse(line.slice(3))}
        </h3>
      );
      i++;
      continue;
    }

    // # Heading 2
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="text-lg font-heading font-bold text-text-primary mt-6 mb-2">
          {inlineParse(line.slice(2))}
        </h2>
      );
      i++;
      continue;
    }

    // Unordered list
    if (/^[-*] /.test(line.trim())) {
      const items = [];
      while (i < lines.length && /^[-*] /.test(lines[i].trim())) {
        items.push(<li key={i} className="text-text-secondary">{inlineParse(lines[i].trim().slice(2))}</li>);
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="list-disc list-inside space-y-1 my-2 ml-1">
          {items}
        </ul>
      );
      continue;
    }

    // Ordered list
    if (/^\d+\. /.test(line.trim())) {
      const items = [];
      while (i < lines.length && /^\d+\. /.test(lines[i].trim())) {
        items.push(<li key={i} className="text-text-secondary">{inlineParse(lines[i].trim().replace(/^\d+\. /, ''))}</li>);
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="list-decimal list-inside space-y-1 my-2 ml-1">
          {items}
        </ol>
      );
      continue;
    }

    // Paragraph (fallback)
    elements.push(
      <p key={i} className="text-text-secondary leading-relaxed my-2">
        {inlineParse(line)}
      </p>
    );
    i++;
  }

  return elements;
}

function inlineParse(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-text-primary font-semibold">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}
