import Link from "next/link";

const Register = () => {
  return (
    <>
      <form className="space-y-6" action="#" method="POST">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Name
          </label>
          <div className="mt-2">
            <input
              id="name"
              name="name"
              type="name"
              autoComplete="name"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-gray-500 sm:text-sm sm:leading-6"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="phone"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Phone Number
          </label>
          <div className="mt-2">
            <input
              id="phone"
              name="phone"
              type="phone"
              autoComplete="phone"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-gray-500 sm:text-sm sm:leading-6"
            />
          </div>
        </div>

        <div>
          <button
            type="submit"
            className="flex w-full justify-center rounded-md bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            Register
          </button>
        </div>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Already have an account?
        <Link
          href="/login"
          className="font-semibold text-green-500 hover:text-green-600 ml-2"
        >
          Sign in
        </Link>
      </p>
    </>
  );
};

export default Register;
