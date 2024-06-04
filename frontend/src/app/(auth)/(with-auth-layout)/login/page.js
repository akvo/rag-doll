import Link from "next/link";

const Login = () => {
  return (
    <>
      <form className="space-y-6" action="#" method="POST">
        <div>
          <label
            for="email"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Phone Number
          </label>
          <div className="mt-2">
            <input
              id="email"
              name="email"
              type="email"
              autocomplete="email"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            />
          </div>
        </div>

        <div>
          <button
            type="submit"
            className="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Sign in
          </button>
        </div>
      </form>

      <p className="mt-10 text-center text-sm text-gray-500">
        Not a member?
        <Link
          href="/register"
          className="font-semibold leading-6 text-indigo-600 hover:text-indigo-500 ml-2"
        >
          Register
        </Link>
      </p>
    </>
  );
};

export default Login;
