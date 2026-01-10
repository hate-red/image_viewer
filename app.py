import flet as ft

import io
import base64
from pathlib import Path
from PIL import Image


def configure_app(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.DARK

    page.expand = True
    page.title = 'Image Viewer'


def main(page: ft.Page) -> None:
    configure_app(page)

    menu_row_height = 50
    tools_row_height = 50
    main_row_height = page.window.height - (menu_row_height + tools_row_height) # type: ignore


    def on_resize(e):
        nonlocal main_row_height
        main_row_height = page.window.height - (menu_row_height + tools_row_height) # type: ignore

        page.update()


    def toggle_visibility() -> None:
        image_block.visible = True
        tools_row.visible = True
        selected_images_text.visible = False
        save_file_btn.disabled = False


    def process_images_paths(images_paths: list) -> None:
        if len(images_paths) > 1:
            swipe_left_btn.visible = True
            swipe_right_btn.visible = True

        nonlocal selected_images, current_image
        selected_images = [Image.open(path) for path in images_paths] # type: ignore
        current_image = selected_images[0]
        image_block.src = convert_to_b64(current_image)


    async def handle_pick_dir(e: ft.Event[ft.Button]) -> None:
        initial_dir = Path('/home/q/Pictures/')
        selected_dir = await ft.FilePicker().get_directory_path(
            dialog_title='Select dir',
            initial_directory=initial_dir.__str__()
        )

        dir = Path(selected_dir) if selected_dir else initial_dir
        images_paths = [
            path for path in dir.iterdir()
            if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp'] 
        ]
        print(dir)
        print(images_paths)

        process_images_paths(images_paths)
        toggle_visibility()

        page.update()


    async def handle_pick_files(e: ft.Event[ft.Button]) -> None:
        images = await ft.FilePicker().pick_files(
            dialog_title='Select image',
            allow_multiple=True,
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
        )
        if not images:
            return
        
        images_paths = [image.path for image in images]

        process_images_paths(images_paths)
        toggle_visibility()

        page.update()


    def convert_to_b64(image):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        
        base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_img


    def update_image(image) -> None:
        base64_img = convert_to_b64(image)        
        
        image_block.src = base64_img
        page.update()


    def apply_left_rotation(e) -> None:
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(90, expand=True)
        update_image(current_image)


    def apply_right_rotation(e) -> None:
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(-90, expand=True)
        update_image(current_image)


    def swipe_left(e):
        nonlocal current_image, current_image_ind

        if current_image_ind <= 0:
            return

        current_image = selected_images[current_image_ind - 1]
        current_image_ind -= 1
        update_image(current_image)


    def swipe_right(e):
        nonlocal current_image, current_image_ind

        if current_image_ind >= len(selected_images) - 1:
            return

        current_image = selected_images[current_image_ind + 1]
        current_image_ind += 1
        update_image(current_image)


    open_files_btn = ft.Button(
        content=ft.Text('Open Image', size=18), 
        on_click=handle_pick_files,
        height=40,
        autofocus=True,
    )
    open_dir_btn = ft.Button(
        content=ft.Text('Open Dir', size=18),
        on_click=handle_pick_dir,
        height=40,
    )
    save_file_btn = ft.Button(
        content=ft.Text('Save Image', size=18), 
        disabled=True,
        height=40,
    )

    selected_images_text = ft.Text(
        value='No files selected', 
        size=24, 
        opacity=0.5
    )
    image_block = ft.Image(
        src='',
        visible=False,
        fit=ft.BoxFit.CONTAIN,
    )
    
    current_image = None
    current_image_ind = 0
    selected_images = []

    swipe_left_btn = ft.IconButton(
        ft.Icons.KEYBOARD_ARROW_LEFT_OUTLINED, 
        on_click=swipe_left,
        icon_size=50, 
        opacity=0.5,
        visible=False,
        height=main_row_height,
        expand=True,
    )
    swipe_right_btn = ft.IconButton(
        ft.Icons.KEYBOARD_ARROW_RIGHT_OUTLINED,
        on_click=swipe_right, 
        icon_size=50, 
        opacity=0.5,
        visible=False,
        height=main_row_height,
        expand=True,
    )

    menu_row = ft.Row(
        controls=[open_files_btn, open_dir_btn, save_file_btn], 
        alignment=ft.MainAxisAlignment.CENTER,
    )

    main_row = ft.Row(
        controls=[
            ft.Column(
                controls=[swipe_left_btn], 
            ),
            selected_images_text,
            image_block,
            ft.Column(
                controls=[swipe_right_btn], 
            ),
        ], 
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
    )

    tools_row = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ROTATE_LEFT, on_click=apply_left_rotation),
            ft.IconButton(ft.Icons.CROP),
            ft.IconButton(ft.Icons.ROTATE_RIGHT, on_click=apply_right_rotation),
        ],
        alignment=ft.MainAxisAlignment.CENTER, 
        visible=False,
    )


    page.add(
        ft.Container(
            content=menu_row,
            alignment=ft.Alignment.TOP_CENTER,
            # border=ft.Border(top=ft.BorderSide(), bottom=ft.BorderSide()),
            height=menu_row_height,
        ),
        ft.Container(
            content=main_row,
            alignment=ft.Alignment.CENTER,
            # border=ft.Border(top=ft.BorderSide(), bottom=ft.BorderSide()),
            height=main_row_height,
            expand=True
        ),
        ft.Container(
            content=tools_row,
            alignment=ft.Alignment.BOTTOM_CENTER,
            # border=ft.Border(top=ft.BorderSide(), bottom=ft.BorderSide()),
            height=tools_row_height
        ),
    )

    page.on_resize = on_resize
    page.update()


if __name__ == "__main__":
    ft.run(main=main)
