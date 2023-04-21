from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import os


# Load images from a directory
def load_images(path):
    images = []
    for f in os.listdir(path):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            try:
                image = Image.open(os.path.join(path, f))
                images.append((f, image))
            except Exception as e:
                print(f"Error loading {f}: {e}")
    return images


# Create columns of image frames from a list of image directories
def create_image_columns(canvas, image_dirs, max_width=200, padding=10):
    columns = []
    for path in image_dirs:
        images = load_images(path)
        column_frames = []
        for img_name, img in images:
            img = resize_and_crop(img, max_width)
            photo = ImageTk.PhotoImage(img)
            frame = Frame(
                canvas,
                bd=2,
                relief="ridge",
                width=max_width,
                height=max_width + padding,
            )
            img_label = Label(frame, image=photo)
            img_label.image = photo
            img_label.pack()
            column_frames.append((img_name, frame))
        columns.append(column_frames)
    return columns


# Handle the start of a drag-and-drop operation
def on_drag_start(event):
    widget = event.widget
    widget.drag_data = {"frame": widget, "x": event.x, "y": event.y}


# Handle the dragging of an image frame
def on_drag(event):
    widget = event.widget
    x, y = widget.drag_data["x"], widget.drag_data["y"]
    dx = event.x - x
    dy = event.y - y
    widget.place(x=widget.winfo_x() + dx, y=widget.winfo_y() + dy)


# Get the bottom position of the last image in a column
def get_bottom_position(column_frames):
    max_y = 0
    for _, frame in column_frames:
        y = frame.winfo_y()
        if y > max_y:
            max_y = y
    return max_y + 210


# Handle the release of an image frame during drag-and-drop
def on_drag_release(event, columns, canvas):
    widget = event.widget
    target_column_index = (widget.winfo_x() + widget.winfo_width() // 2) // 210
    if 0 <= target_column_index < len(columns):
        source_column = None
        source_index = None
        for column in columns:
            for idx, (img_name, frame) in enumerate(column):
                if frame == widget:
                    source_column = column
                    source_index = idx
                    break
            if source_column:
                break

        if source_column is not None:
            # Find the source_column_index
            for idx, column in enumerate(columns):
                if column == source_column:
                    source_column_index = idx
                    break

            if source_column_index == target_column_index:
                canvas.create_window(
                    210 * source_column_index,
                    (210 * source_index + source_index * 10) + 50 * (source_index + 1),
                    window=widget,
                    anchor="nw",
                )
                return

            source_column.remove((img_name, widget))

            # Move up images in the source column to close the gap
            for idx, (_, frame) in enumerate(
                source_column[source_index:], start=source_index
            ):
                canvas.create_window(
                    210 * source_column_index,
                    (210 * idx + idx * 10) + 50 * (idx + 1),
                    window=frame,
                    anchor="nw",
                )

        target_column = columns[target_column_index]
        insert_position = None
        if not target_column:  # empty column
            insert_position = 0
            target_y = 50
        else:
            target_y = (
                get_bottom_position(target_column) + 50
            )  # Add 50 to place at the bottom
            insert_position = len(target_column)

        widget.place_forget()
        canvas.create_window(
            210 * target_column_index, target_y, window=widget, anchor="nw"
        )

        target_column.insert(
            insert_position if insert_position is not None else len(target_column),
            (img_name, widget),
        )

        # Re-adjust the positions of the images below the inserted image in the target column
        for idx, (_, frame) in enumerate(
            target_column[insert_position + 1 :], start=insert_position + 1
        ):
            canvas.create_window(
                210 * target_column_index,
                (210 * idx + idx * 10) + 50,
                window=frame,
                anchor="nw",
            )

    update_canvas_scrollregion(columns, canvas)


# Bind drag-and-drop events to an image frame
def bind_drag_and_drop(widget, canvas, columns):
    widget.canvas = canvas
    widget.drag_data = {}
    widget.bind("<ButtonPress-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag)
    widget.bind(
        "<ButtonRelease-1>", lambda event: on_drag_release(event, columns, canvas)
    )


def resize_and_crop(image, size):
    width, height = image.size
    aspect_ratio = float(width) / float(height)

    if aspect_ratio > 1:
        new_width = size
        new_height = int(size / aspect_ratio)
    else:
        new_width = int(size * aspect_ratio)
        new_height = size

    image = image.resize((new_width, new_height), Image.ANTIALIAS)

    width, height = image.size
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2

    return image.crop((left, top, right, bottom))


# Delete an image frame from the canvas TODO make this move the images and fix bug when dragging fter scroll
def delete_image(image_frame, columns, canvas):
    source_column = None
    source_index = None
    for column in columns:
        for idx, (img_name, frame) in enumerate(column):
            if frame == image_frame:
                source_column = column
                source_index = idx
                break
        if source_column:
            break

    if source_column:
        source_column.remove((img_name, image_frame))

        # Move up images in the source column to close the gap
        for idx, (_, frame) in enumerate(
            source_column[source_index:], start=source_index
        ):
            canvas.create_window(
                210 * columns.index(source_column),
                (210 * idx + idx * 10) + 50 * (idx + 1),
                window=frame,
                anchor="nw",
            )

        image_frame.destroy()
        update_canvas_scrollregion(columns, canvas)



# Enlarge an image in a separate window
def enlarge_image(image_path):
    enlarged_img = Image.open(image_path)
    photo = ImageTk.PhotoImage(enlarged_img)
    top = Toplevel()
    top.title("Enlarged Image")
    img_label = Label(top, image=photo)
    img_label.image = photo
    img_label.pack()


def update_canvas_scrollregion(columns, canvas):
    max_y = 0
    max_x = 210 * len(columns)
    for column_frames in columns:
        bottom_y = get_bottom_position(column_frames) + 50
        if bottom_y > max_y:
            max_y = bottom_y
    canvas.configure(scrollregion=(0, 0, max_x, max_y + (210 * len(columns))))


# Main function
def main():
    image_dirs = [
        "images/1",
        "images/2",
        "images/3",
    ]

    # Create the main window and set its title and size
    root = Tk()
    root.title("Image Organizer")
    root.geometry("800x800")
    root.resizable(False, False)

    container = Frame(root)
    container.pack(side="left", fill="both", expand=True)

    # Create a canvas and scrollbar for smooth scrolling through the images
    canvas = Canvas(container, bg="white", width=800, height=800)
    scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    columns = create_image_columns(canvas, image_dirs)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Create a new frame inside the canvas for placing the images
    canvas_frame = Frame(canvas)
    canvas.create_window((0, 0), window=canvas_frame, anchor="nw")

    # Draw black lines separating the columns
    for i in range(1, len(columns)):
        canvas.create_line(i * 210, 0, i * 210, 10000, fill="black", width=2)

    # Place the image frames in the canvas_frame and add drag-and-drop and delete/enlarge functionality
    for i, column in enumerate(columns):
        for j, (img_name, frame) in enumerate(column):
            bind_drag_and_drop(frame, canvas, columns)
            delete_button = Button(
                frame,
                text="X",
                command=lambda f=frame: delete_image(f, columns, canvas),
            )
            delete_button.pack(side="left", padx=5)
            enlarge_button = Button(
                frame,
                text="Enlarge",
                command=lambda path=os.path.join(
                    image_dirs[i], img_name
                ): enlarge_image(path),
            )
            enlarge_button.pack(side="left", padx=5)
            canvas.create_window(
                i * 210, 50 + j * (210 + 50) + j * 10, window=frame, anchor="nw"
            )

    update_canvas_scrollregion(columns, canvas)

    # Resize the canvas when the main window is resized
    def on_resize(event):
        canvas.configure(width=event.width, height=event.height)

    root.bind("<Configure>", on_resize)

    # Start the main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
