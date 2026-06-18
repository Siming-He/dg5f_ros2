#!/usr/bin/env python3

import argparse
import math
import sys
import tkinter as tk
from tkinter import ttk

import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


JOINT_LIMITS = [
    ("rj_dg_1_1", -0.3839724354387525, 0.8901179185171081),
    ("rj_dg_1_2", -math.pi, 0.0),
    ("rj_dg_1_3", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_1_4", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_2_1", -0.4188790204786391, 0.6108652381980153),
    ("rj_dg_2_2", 0.0, 2.007128639793479),
    ("rj_dg_2_3", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_2_4", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_3_1", -0.6108652381980153, 0.6108652381980153),
    ("rj_dg_3_2", 0.0, 1.9547687622336491),
    ("rj_dg_3_3", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_3_4", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_4_1", -0.6108652381980153, 0.4188790204786391),
    ("rj_dg_4_2", 0.0, 1.9024088846738192),
    ("rj_dg_4_3", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_4_4", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_5_1", -0.017453292519943295, 1.0471975511965976),
    ("rj_dg_5_2", -0.4188790204786391, 0.6108652381980153),
    ("rj_dg_5_3", -math.pi / 2.0, math.pi / 2.0),
    ("rj_dg_5_4", -math.pi / 2.0, math.pi / 2.0),
]


class Dg5fCommandNode(Node):
    def __init__(self, namespace, controller):
        super().__init__("dg5f_right_control_panel")
        namespace = namespace.strip("/")
        self.joint_names = [joint[0] for joint in JOINT_LIMITS]
        self.position_topic = f"/{namespace}/{controller}/joint_trajectory"
        self.effort_topic = f"/{namespace}/effort_controller/commands"
        self.position_pub = self.create_publisher(
            JointTrajectory, self.position_topic, 10
        )
        self.effort_pub = self.create_publisher(Float64MultiArray, self.effort_topic, 10)

    def publish_position(self, positions, duration_sec):
        msg = JointTrajectory()
        msg.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = positions
        sec = int(duration_sec)
        point.time_from_start = Duration(
            sec=sec, nanosec=int((duration_sec - sec) * 1_000_000_000)
        )

        msg.points.append(point)
        self.position_pub.publish(msg)
        self.get_logger().info(f"Published joint target to {self.position_topic}")

    def publish_effort(self, efforts):
        msg = Float64MultiArray()
        msg.data = efforts
        self.effort_pub.publish(msg)


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.window, width=event.width),
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


def apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    bg = "#f5f7fb"
    panel = "#ffffff"
    border = "#d6dbe6"
    text = "#1f2937"
    accent = "#2563eb"

    root.configure(bg=bg)
    style.configure(".", font=("TkDefaultFont", 10), background=bg, foreground=text)
    style.configure("TFrame", background=bg)
    style.configure("Panel.TFrame", background=panel, relief="solid", borderwidth=1)
    style.configure("TLabel", background=bg, foreground=text)
    style.configure("Panel.TLabel", background=panel, foreground=text)
    style.configure("Muted.TLabel", background=bg, foreground="#667085")
    style.configure("PanelMuted.TLabel", background=panel, foreground="#667085")
    style.configure("Title.TLabel", font=("TkDefaultFont", 14, "bold"))
    style.configure("TButton", padding=(10, 5))
    style.configure("Primary.TButton", foreground="#ffffff", background=accent)
    style.map("Primary.TButton", background=[("active", "#1d4ed8")])
    style.configure("TNotebook", background=bg, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 7))
    style.configure("TLabelframe", background=bg, bordercolor=border)
    style.configure("TLabelframe.Label", background=bg, foreground=text)
    style.configure(
        "Horizontal.TScale",
        background=panel,
        troughcolor="#e5e7eb",
        sliderthickness=18,
    )


def clamp(value, lower, upper):
    return min(max(value, lower), upper)


class PositionPanel:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title("DG5F Right Joint Targets")
        self.root.geometry("900x620")
        self.root.minsize(760, 520)
        apply_style(self.root)

        self.auto_publish = tk.BooleanVar(value=False)
        self.duration = tk.DoubleVar(value=2.0)
        self.joint_vars = []
        self.radian_vars = []
        self._auto_after = None

        for index, (_, lower, upper) in enumerate(JOINT_LIMITS):
            var = tk.DoubleVar(value=0.0)
            rad_var = tk.StringVar()
            var.trace_add("write", lambda *_args, i=index: self._value_changed(i))
            self.joint_vars.append(var)
            self.radian_vars.append(rad_var)

        self._build()
        for index in range(len(JOINT_LIMITS)):
            self._value_changed(index, publish=False)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        header = ttk.Frame(self.root, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="DG5F Right Joint Targets", style="Title.TLabel").pack(
            side="left"
        )
        ttk.Label(header, text=self.node.position_topic, style="Muted.TLabel").pack(
            side="right"
        )

        controls = ttk.Frame(self.root, padding=(16, 0, 16, 10))
        controls.pack(fill="x")
        controls.columnconfigure(10, weight=1)
        ttk.Label(controls, text="Duration (s)").pack(side="left")
        ttk.Spinbox(
            controls,
            from_=0.1,
            to=10.0,
            increment=0.1,
            width=5,
            textvariable=self.duration,
        ).pack(side="left", padx=(6, 16))
        ttk.Button(
            controls, text="Publish", command=self._publish, style="Primary.TButton"
        ).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(
            controls, text="Auto publish", variable=self.auto_publish
        ).pack(side="left", padx=(0, 18))
        ttk.Button(controls, text="Open", command=self._zero).pack(side="left")
        ttk.Button(controls, text="Half", command=self._mid).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(controls, text="Close", command=self._max_flex).pack(
            side="left", padx=(6, 0)
        )

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        all_tab = ttk.Frame(notebook, padding=10)
        notebook.add(all_tab, text="All")
        scroll = ScrollFrame(all_tab)
        scroll.pack(fill="both", expand=True)
        scroll.inner.columnconfigure(0, weight=1)
        for finger in range(5):
            group = ttk.LabelFrame(scroll.inner, text=f"Finger {finger + 1}", padding=8)
            group.grid(row=finger, column=0, sticky="ew", pady=(0, 8))
            group.columnconfigure(1, weight=1)
            self._build_finger_rows(group, finger)

        for finger in range(5):
            tab = ttk.Frame(notebook, padding=16)
            notebook.add(tab, text=f"Finger {finger + 1}")
            tab.columnconfigure(0, weight=1)
            self._build_finger_presets(tab, finger).grid(
                row=0, column=0, sticky="ew", pady=(0, 14)
            )
            panel = ttk.Frame(tab, padding=12, style="Panel.TFrame")
            panel.grid(row=1, column=0, sticky="nsew")
            panel.columnconfigure(1, weight=1)
            self._build_finger_rows(panel, finger)

    def _build_finger_presets(self, parent, finger):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text=f"Finger {finger + 1}", style="Title.TLabel").pack(
            side="left"
        )
        ttk.Button(
            frame, text="Open finger", command=lambda: self._zero_finger(finger)
        ).pack(side="right")
        ttk.Button(
            frame, text="Half finger", command=lambda: self._mid_finger(finger)
        ).pack(side="right", padx=(0, 6))
        ttk.Button(
            frame, text="Close finger", command=lambda: self._max_flex_finger(finger)
        ).pack(side="right", padx=(0, 6))
        return frame

    def _build_finger_rows(self, parent, finger):
        for joint_offset in range(4):
            index = finger * 4 + joint_offset
            self._build_joint_row(parent, index, joint_offset)

    def _build_joint_row(self, parent, index, row):
        name, lower, upper = JOINT_LIMITS[index]
        lower_deg = math.degrees(lower)
        upper_deg = math.degrees(upper)

        ttk.Label(parent, text=name, width=12).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=7
        )
        scale = ttk.Scale(
            parent,
            from_=lower_deg,
            to=upper_deg,
            variable=self.joint_vars[index],
            orient="horizontal",
            command=lambda _value, i=index: self._value_changed(i),
        )
        scale.grid(row=row, column=1, sticky="ew", pady=7)
        spin = ttk.Spinbox(
            parent,
            from_=lower_deg,
            to=upper_deg,
            increment=0.5,
            width=8,
            textvariable=self.joint_vars[index],
            command=lambda i=index: self._value_changed(i),
            format="%.1f",
        )
        spin.grid(row=row, column=2, sticky="e", padx=(10, 4), pady=7)
        ttk.Label(parent, text="deg").grid(row=row, column=3, sticky="w", pady=7)
        ttk.Label(parent, textvariable=self.radian_vars[index], width=10).grid(
            row=row, column=4, sticky="e", padx=(12, 0), pady=7
        )
        spin.bind("<Return>", lambda _event, i=index: self._value_changed(i))
        spin.bind("<FocusOut>", lambda _event, i=index: self._value_changed(i))

    def _value_changed(self, index, publish=True):
        value = self._degrees(index)
        self.radian_vars[index].set(f"{math.radians(value): .3f} rad")
        if publish:
            self._schedule_auto_publish()

    def _schedule_auto_publish(self):
        if self.auto_publish.get():
            if self._auto_after is not None:
                self.root.after_cancel(self._auto_after)
            self._auto_after = self.root.after(150, self._publish)

    def _degrees(self, index):
        _, lower, upper = JOINT_LIMITS[index]
        lower_deg = math.degrees(lower)
        upper_deg = math.degrees(upper)
        try:
            raw_value = float(self.joint_vars[index].get())
        except (tk.TclError, ValueError):
            raw_value = 0.0
        value = clamp(raw_value, lower_deg, upper_deg)
        if abs(value - raw_value) > 1e-9:
            self.joint_vars[index].set(value)
        return value

    def _positions(self):
        return [math.radians(self._degrees(index)) for index in range(len(JOINT_LIMITS))]

    def _publish(self):
        self._auto_after = None
        self.node.publish_position(self._positions(), max(0.1, self.duration.get()))

    def _set_degrees(self, indexes, values):
        for index, value in zip(indexes, values):
            _, lower, upper = JOINT_LIMITS[index]
            self.joint_vars[index].set(
                clamp(value, math.degrees(lower), math.degrees(upper))
            )
        self._schedule_auto_publish()

    def _finger_indexes(self, finger):
        start = finger * 4
        return list(range(start, start + 4))

    def _zero(self):
        self._set_degrees(list(range(len(JOINT_LIMITS))), [0.0] * len(JOINT_LIMITS))

    def _mid(self):
        values = []
        for _, lower, upper in JOINT_LIMITS:
            values.append(math.degrees((lower + upper) / 2.0))
        self._set_degrees(list(range(len(JOINT_LIMITS))), values)

    def _max_flex(self):
        values = [math.degrees(upper) for _, _, upper in JOINT_LIMITS]
        self._set_degrees(list(range(len(JOINT_LIMITS))), values)

    def _zero_finger(self, finger):
        indexes = self._finger_indexes(finger)
        self._set_degrees(indexes, [0.0] * 4)

    def _mid_finger(self, finger):
        indexes = self._finger_indexes(finger)
        values = [
            math.degrees((JOINT_LIMITS[index][1] + JOINT_LIMITS[index][2]) / 2.0)
            for index in indexes
        ]
        self._set_degrees(indexes, values)

    def _max_flex_finger(self, finger):
        indexes = self._finger_indexes(finger)
        values = [math.degrees(JOINT_LIMITS[index][2]) for index in indexes]
        self._set_degrees(indexes, values)

    def _close(self):
        if self._auto_after is not None:
            self.root.after_cancel(self._auto_after)
        self.root.destroy()
        self.node.destroy_node()
        rclpy.shutdown()

    def run(self):
        self.root.mainloop()


class EffortPanel:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title("DG5F Right Hold-to-Send Effort")
        self.root.geometry("760x520")
        self.root.minsize(640, 460)
        apply_style(self.root)

        self.effort = tk.DoubleVar(value=0.001)
        self.status = tk.StringVar(value="Idle: publishing zero effort")
        self.active = False
        self.joint_enabled = [tk.BooleanVar(value=True) for _ in JOINT_LIMITS]

        self._build()
        self.root.bind("<ButtonRelease-1>", self._release)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        header = ttk.Frame(self.root, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="DG5F Right Effort", style="Title.TLabel").pack(
            side="left"
        )
        ttk.Label(header, text=self.node.effort_topic, style="Muted.TLabel").pack(
            side="right"
        )

        effort_frame = ttk.Frame(self.root, padding=(16, 0, 16, 10))
        effort_frame.pack(fill="x")
        ttk.Label(effort_frame, text="Effort").pack(side="left")
        scale = ttk.Scale(
            effort_frame,
            variable=self.effort,
            from_=-0.01,
            to=0.01,
            orient="horizontal",
        )
        scale.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Spinbox(
            effort_frame,
            from_=-0.01,
            to=0.01,
            increment=0.0001,
            width=9,
            textvariable=self.effort,
            format="%.4f",
        ).pack(side="left")

        hold = tk.Button(
            self.root,
            text="HOLD TO SEND EFFORT",
            height=3,
            font=("TkDefaultFont", 12, "bold"),
            fg="#ffffff",
            bg="#16a34a",
            activeforeground="#ffffff",
            activebackground="#15803d",
            relief="flat",
            cursor="hand2",
        )
        hold.pack(fill="x", padx=16, pady=(0, 8))
        hold.bind("<ButtonPress-1>", self._press)
        hold.bind("<ButtonRelease-1>", self._release)
        ttk.Label(self.root, textvariable=self.status, style="Muted.TLabel").pack(
            fill="x", padx=16, pady=(0, 10)
        )

        buttons = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="All joints", command=self._select_all).pack(
            side="left"
        )
        ttk.Button(buttons, text="Clear", command=self._clear).pack(
            side="left", padx=6
        )

        panel = ttk.Frame(self.root, padding=12, style="Panel.TFrame")
        panel.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for finger in range(5):
            group = ttk.LabelFrame(panel, text=f"Finger {finger + 1}", padding=8)
            group.grid(row=finger, column=0, sticky="ew", pady=(0, 6))
            panel.columnconfigure(0, weight=1)
            ttk.Button(
                group, text="All", command=lambda f=finger: self._select_finger(f)
            ).grid(row=0, column=0, padx=(0, 8))
            ttk.Button(
                group, text="None", command=lambda f=finger: self._clear_finger(f)
            ).grid(row=0, column=1, padx=(0, 12))
            for joint_offset in range(4):
                index = finger * 4 + joint_offset
                name = JOINT_LIMITS[index][0]
                ttk.Checkbutton(
                    group, text=name, variable=self.joint_enabled[index]
                ).grid(row=0, column=joint_offset + 2, padx=8, sticky="w")

    def _press(self, _):
        self.active = True
        self.status.set(f"Active: sending {self.effort.get():.4f} to selected joints")

    def _release(self, _):
        self.active = False
        self.status.set("Idle: publishing zero effort")
        self.node.publish_effort([0.0] * len(JOINT_LIMITS))

    def _select_all(self):
        for var in self.joint_enabled:
            var.set(True)

    def _clear(self):
        for var in self.joint_enabled:
            var.set(False)

    def _select_finger(self, finger):
        for index in range(finger * 4, finger * 4 + 4):
            self.joint_enabled[index].set(True)

    def _clear_finger(self, finger):
        for index in range(finger * 4, finger * 4 + 4):
            self.joint_enabled[index].set(False)

    def _tick(self):
        if self.active:
            try:
                value = float(self.effort.get())
            except (tk.TclError, ValueError):
                value = 0.0
            efforts = [
                value if enabled.get() else 0.0 for enabled in self.joint_enabled
            ]
            self.status.set(f"Active: sending {value:.4f} to selected joints")
        else:
            efforts = [0.0] * len(JOINT_LIMITS)
        self.node.publish_effort(efforts)
        self.root.after(20, self._tick)

    def _close(self):
        self.active = False
        self.node.publish_effort([0.0] * len(JOINT_LIMITS))
        self.root.destroy()
        self.node.destroy_node()
        rclpy.shutdown()

    def run(self):
        self._tick()
        self.root.mainloop()


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("position", "effort"), default="position"
    )
    parser.add_argument("--namespace", default="dg5f_right")
    parser.add_argument("--controller", default="dg5f_right_controller")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    rclpy.init()
    node = Dg5fCommandNode(args.namespace, args.controller)
    panel = EffortPanel(node) if args.mode == "effort" else PositionPanel(node)
    panel.run()


if __name__ == "__main__":
    main()
