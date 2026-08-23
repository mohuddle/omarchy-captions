import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "io.github.mohuddle.captions"
  ipcTarget: "io.github.mohuddle.captions"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  property var service: null
  readonly property var barIdentity: hostWidget || root
  readonly property color foreground: bar ? bar.foreground : Color.foreground
  readonly property color muted: Color.muted
  readonly property color accent: Color.accent
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family

  function closeForPopoutSwitch() {}
  function open() { controller.show() }
  function close() { controller.hide() }
  function toggle() { if (opened) close(); else open() }
  function switchPanel(direction) { return false }

  readonly property int pinTopMargin: {
    if (root.bar && root.bar.position === "top")
      return (root.bar.barSize || Style.bar.sizeHorizontal) + Style.gapsOut
    return Style.gapsOut
  }
  readonly property int pinRightMargin: {
    if (root.bar && root.bar.position === "right")
      return (root.bar.barSize || Style.bar.sizeHorizontal) + Style.gapsOut
    return Style.gapsOut
  }

  PanelWindow {
    id: panel
    visible: root.opened
    implicitWidth: Style.space(480)
    implicitHeight: Style.space(360)
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0

    WlrLayershell.namespace: "captions"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

    anchors.top: true
    anchors.right: true
    margins.top: root.pinTopMargin
    margins.right: root.pinRightMargin

    BorderSurface {
      id: card
      anchors.fill: parent
      color: Color.popups.background
      borderSpec: Border.surfaceSpec("popups", "border", Color.popups.border, Math.max(1, Style.space(2)))
      radius: Style.cornerRadius
      padding: Style.spacing.popupPadding

      PanelKeyCatcher {
        anchors.fill: parent
        anchors.topMargin: card.contentTopInset
        anchors.rightMargin: card.contentRightInset
        anchors.bottomMargin: card.contentBottomInset
        anchors.leftMargin: card.contentLeftInset
        onCloseRequested: root.close()
        onTabRequested: function(direction) { root.switchPanel(direction) }

        Column {
          anchors.fill: parent
          spacing: Style.space(10)

          Row {
            width: parent.width
            spacing: Style.space(10)
            CaptionsIcon {
              size: Style.space(28)
              foreground: root.accent
              anchors.verticalCenter: parent.verticalCenter
            }
            Column {
              spacing: Style.space(2)
              Text {
                textFormat: Text.PlainText
                text: "Captions"
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
              }
              Text {
                textFormat: Text.PlainText
                text: service && service.listening ? "Listening to speakers" : (service && service.error ? service.error : "Idle")
                color: service && service.listening ? root.accent : root.muted
                font.family: root.fontFamily
                font.pixelSize: Style.font.caption
                width: Style.space(360)
                wrapMode: Text.Wrap
              }
            }
          }

          Row {
            spacing: Style.space(8)
            Button {
              text: service && service.listening ? "Stop" : "Listen"
              bordered: true
              foreground: root.foreground
              onClicked: if (service) service.toggle()
            }
            Button {
              text: "Save"
              bordered: true
              foreground: root.foreground
              onClicked: if (service) service.save()
            }
            Button {
              text: "Clear"
              bordered: true
              foreground: root.foreground
              onClicked: if (service) service.clear()
            }
            Button {
              text: "TUI"
              bordered: true
              foreground: root.foreground
              onClicked: if (service) service.openTui()
            }
          }

          Flickable {
            width: parent.width
            height: parent.height - Style.space(110)
            clip: true
            contentWidth: width
            contentHeight: body.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            Text {
              id: body
              width: parent.width
              textFormat: Text.PlainText
              text: service && service.transcript !== "" ? service.transcript : "Play something. Listen captures the speakers, not a URL."
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
              wrapMode: Text.Wrap
              opacity: service && service.transcript !== "" ? 1 : 0.55
            }
          }
        }
      }
    }
  }
}
