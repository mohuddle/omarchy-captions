import QtQuick

Item {
  id: root
  property color foreground: "#e6e1d3"
  property int size: 18
  width: size
  height: size

  Rectangle {
    anchors.centerIn: parent
    width: Math.round(root.size * 0.86)
    height: Math.round(root.size * 0.64)
    radius: Math.max(2, Math.round(root.size * 0.12))
    color: "transparent"
    border.color: root.foreground
    border.width: Math.max(1, Math.round(root.size * 0.08))

    Column {
      anchors.centerIn: parent
      spacing: Math.max(1, Math.round(root.size * 0.08))
      Rectangle {
        width: Math.round(root.size * 0.46)
        height: Math.max(1, Math.round(root.size * 0.08))
        radius: height
        color: root.foreground
      }
      Rectangle {
        width: Math.round(root.size * 0.32)
        height: Math.max(1, Math.round(root.size * 0.08))
        radius: height
        color: root.foreground
        anchors.horizontalCenter: parent.horizontalCenter
      }
    }
  }
}
