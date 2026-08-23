.pragma library

function parseStatus(raw) {
  var empty = {
    ok: false,
    ready: false,
    listening: false,
    model: "",
    source: "speakers",
    partial: "",
    lines: [],
    error: "",
    saved: "",
    lastError: ""
  }
  try {
    var data = JSON.parse(String(raw || "").trim() || "{}")
  } catch (err) {
    empty.lastError = "Could not parse captions status"
    return empty
  }
  return {
    ok: true,
    ready: data.ready === true,
    listening: data.listening === true,
    model: String(data.model || ""),
    source: String(data.source || "speakers"),
    partial: String(data.partial || ""),
    lines: Array.isArray(data.lines) ? data.lines.map(function(line) { return String(line) }) : [],
    error: String(data.error || ""),
    saved: String(data.saved || ""),
    lastError: ""
  }
}

function transcript(status) {
  var lines = (status && status.lines) ? status.lines.slice() : []
  if (status && status.partial) lines.push(status.partial)
  return lines.join("\n")
}
