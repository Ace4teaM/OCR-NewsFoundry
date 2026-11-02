import { NextResponse } from "next/server";

export function proxy(request) {
    const token = request.cookies.get("access_token")?.value;
    const { pathname } = request.nextUrl;

    // Utilisateur non authentifié sur une page protégée
    if (!token && pathname !== "/login") {
        return NextResponse.redirect(
            new URL("/login", request.url)
        );
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        "/((?!api|_next/static|_next/image|favicon.ico).*)",
    ],
};