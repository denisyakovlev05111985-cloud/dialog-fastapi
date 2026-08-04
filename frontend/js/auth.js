const mode = document.body.dataset.authPage;
const isLogin = mode === "login";
const page = {
    title: isLogin ? "Войти в Dialog": "Создать аккаунт",
    subtitle: isLogin 
        ? "Продолжите работу со своими чатами"
        : "Один аккаунт для истории чатов",
    endpoint: isLogin ? "/api/auth/login": "/api/auth/register",
    submit: isLogin ? "Продолжить" : "Создать аккаунт",
    link: isLogin
        ? 'Нет аккаунта <a href="/register.html" class="font-medium text-ink underline">Зарегестрироваться</a>'
        : 'Уже есть аккаунт? <a href="/login.html" class="font-medium text-ink underline">Войти</a>'
};

const nameField = isLogin
    ? ""
    :  `<label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-stone-700">Имя</span>
            <input 
                type="text" 
                class="w-full h-11 rounded-lg border border-stone-300 px-3 text-sm focus:border-stone-700 focus:outline-none"
                name="name"
                minlength="2"
                maxlength="80"
                placeholder="Как к вам обращаться"
                required
                autofocus
            />
        </label>
    `

document.getElementById("authApp").innerHTML = `
    <main class="auth-grid grid min-h-screen place-items-center px-5 py-10">
        <div class="w-full max-w-sm">
            <a href="/" class="mb-8 inline-flex items-center text-int no-underline">
                <span class="text-base font-semibold">Dialog</span>
            </a>

            <section class="rounded-2xl font-semibold border border-stone-200 bg-white p-7 shadow-soft">
                <header class="mb-6">
                    <h1 class="text-2xl font-semibold">${page.title}</h1>

                    <p class="mt-2 leading-6 text-muted">${page.subtitle}</p>
                </header>

                <div id="formError" class="mt-4 hidden rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-red-700" role="alert"></div>

                <form id="authForm" class="space-y-4">
                    ${nameField}

                <label class="block">
                    <span class="mb-1.5 block text-xs font-semibold text-stone-700">Email</span>
                    
                    <input 
                        type="email" 
                        class="w-full h-11 rounded-lg border border-stone-300 px-3 text-sm focus:border-stone-700 focus:outline-none"
                        name="email"
                        placeholder="name@example.com"
                        required
                        ${isLogin ? "autofocus" : ""}
                    />
                </label>

                <label class="block">
                    <span class="mb-1.5 block text-xs font-semibold text-stone-700">Пароль</span>
                    <span class="block relative">
                    <input 
                        type="password" 
                        class="w-full h-11 rounded-lg border border-stone-300 px-3 text-sm focus:border-stone-700 focus:outline-none"
                        name="password"
                        placeholder="${isLogin ? "Ваш пароль": "Не менее 8 символов"}"
                        required
                        minlength="${isLogin ? 1 : 8}"
                        maxlength="128"
                        ${isLogin ? "autofocus" : ""}
                    />

                    <button
                        type="button"
                        id="passwordToggle"
                        class="absolute inset-y-0 right-0 px-3 text-xs font-medium text-stone-500">Показать</button>
                    </span>
                </label>

                <button 
                    type="submit" 
                    class="flex h-11 w-full items-center justify-center rounded-lg bg-stone-900 px-4 font-medium text-white hover:bg-black disabled:opacity-60"
                >${page.submit}</button>
             </form>

             <p class="mt-5 text-center text-sm text-muted">${page.link}</p>
        </section>
    </div>
</main>
`;

const form = document.getElementById("authForm");
const errorBlock = document.getElementById("formError");
const passwordToggle = document.getElementById("passwordToggle");

passwordToggle.addEventListener("click", () => {
    const input = form.elements.password;
    input.type = input.type === "password" ? "text" : "password";
    passwordToggle.textContent = input.type === "password" ? "Показать" : "Скрыть";
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBlock.classList.add("hidden");

    const button = form.querySelector("button[type='submit']");
    button.disable = true;

    try {
        await api(
            page.endpoint,
            { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(form).entries())) }
        );
        window.location.assign("/");
    } catch(e) {
        console.log(e)
        errorBlock.textContent = console.error.message;
        errorBlock.classList.remove("hidden")
    } finally {
        button.disable = false;
    }
});