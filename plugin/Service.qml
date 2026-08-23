import QtQuick
import Quickshell
import Quickshell.Io
import "Model.js" as Model

Item {
  id: root

  property var settings: ({})
  readonly property string home: Quickshell.env("HOME")
  readonly property string statusFile: home + "/.local/state/omarchy/captions/status.json"
  readonly property string bin: home + "/.local/bin/captions"

  property bool ready: false
  property bool listening: false
  property string model: ""
  property string source: "speakers"
  property string partial: ""
  property var lines: []
  property string error: ""
  property string saved: ""
  property string lastError: ""
  property string statusText: "Captions"

  readonly property string transcript: Model.transcript({ lines: root.lines, partial: root.partial })

  function apply(raw) {
    var parsed = Model.parseStatus(raw)
    if (!parsed.ok) {
      lastError = parsed.lastError
      return
    }
    ready = parsed.ready
    listening = parsed.listening
    model = parsed.model
    source = parsed.source
    partial = parsed.partial
    lines = parsed.lines
    error = parsed.error
    saved = parsed.saved
    lastError = parsed.error
    statusText = listening ? "Captions on" : (ready ? "Captions" : "Captions setup")
  }

  function run(args) {
    if (cmd.running) return
    cmd.command = [root.bin].concat(args)
    cmd.running = true
  }

  function toggle() { run([root.listening ? "stop" : "start"]) }
  function start() { run(["start"]) }
  function stop() { run(["stop"]) }
  function clear() { run(["clear"]) }
  function save() { run(["save"]) }
  function refresh() { run(["status"]) }
  function openTui() {
    tui.command = ["xdg-terminal-exec", root.bin, "tui"]
    tui.running = true
  }

  FileView {
    id: statusView
    path: root.statusFile
    watchChanges: true
    printErrors: false
    onLoaded: root.apply(text())
    onLoadFailed: root.lastError = ""
    onFileChanged: reload()
  }

  Process {
    id: cmd
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.apply(text)
    }
  }

  Process { id: tui }

  Timer {
    interval: 2000
    running: true
    repeat: true
    onTriggered: {
      if (!root.ready && !cmd.running) root.refresh()
    }
  }

  Component.onCompleted: refresh()
}
