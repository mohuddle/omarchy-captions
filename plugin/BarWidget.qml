import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "io.github.mohuddle.captions"

  Service {
    id: captions
    settings: root.settings
  }

  readonly property color barForeground: bar ? bar.barForeground : Color.foreground
  readonly property color iconColor: captions.listening ? Color.accent : (
    captions.error !== "" ? Qt.darker(barForeground, 1.2) : barForeground
  )
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false
  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function open() {
    if (panelLoader.item) panelLoader.item.open()
  }
  function close() {
    if (panelLoader.item) panelLoader.item.close()
  }
  function togglePanel() {
    if (panelLoader.item) panelLoader.item.toggle()
  }
  function closeForPopoutSwitch() {}
  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
    if ("service" in target) target.service = captions
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight
  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  IpcHandler {
    target: "io.github.mohuddle.captions"
    function open(): void { root.open() }
    function close(): void { root.close() }
    function show(): void { root.open() }
    function hide(): void { root.close() }
    function toggle(): void { root.togglePanel() }
    function start(): void { captions.start() }
    function stop(): void { captions.stop() }
    function status(): string { return captions.statusText }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    tooltipText: captions.listening ? "Captions on" : "Captions"
    foreground: root.iconColor
    iconComponent: Component {
      CaptionsIcon {
        anchors.fill: parent
        foreground: button.foreground
        size: Math.min(width, height)
      }
    }
    onPressed: function(b) {
      if (b === Qt.LeftButton) root.togglePanel()
      if (b === Qt.RightButton) captions.toggle()
    }
  }
}
